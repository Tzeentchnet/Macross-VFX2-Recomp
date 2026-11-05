#include "mod_plugins.h"
#include "cpu_state.h"
#include "psx_sdl.h"

#include <stdio.h>
#include <string.h>

#define MACROSS_DEBUG_MENU_HOOK 0x8001A7D8u
#define MACROSS_DEBUG_MENU_RUNNER 0x80025468u
#define MACROSS_DEBUG_MENU_ROOT 0x800801C0u
#define MACROSS_DEBUG_MENU_RETURN 0x0F000100u

static SDL_atomic_t macross_debug_menu_requested;
static SDL_atomic_t macross_debug_menu_enabled;
static SDL_atomic_t macross_debug_menu_active;
static SDL_atomic_t macross_debug_menu_verified;
static int macross_debug_menu_watch_installed;
static uint32_t macross_debug_menu_resume_gpr[5];

enum {
    MACROSS_DEBUG_MENU_IDLE = 0,
    MACROSS_DEBUG_MENU_OPENING,
    MACROSS_DEBUG_MENU_RUNNING,
    MACROSS_DEBUG_MENU_RESUMING
};

static int macross_debug_menu_phase;

#if defined(PSX_SDL3)
static bool SDLCALL macross_debug_menu_event_watch(void* userdata,
                                                   SDL_Event* event)
#else
static int SDLCALL macross_debug_menu_event_watch(void* userdata,
                                                  SDL_Event* event)
#endif
{
    (void)userdata;
    if (event->type == SDL_KEYDOWN && !event->key.repeat) {
#if defined(PSX_SDL3)
        const SDL_Scancode scancode = event->key.scancode;
#else
        const SDL_Scancode scancode = event->key.keysym.scancode;
#endif
        if (scancode == SDL_SCANCODE_F12 &&
            SDL_AtomicGet(&macross_debug_menu_enabled) &&
            !SDL_AtomicGet(&macross_debug_menu_active)) {
            SDL_AtomicSet(&macross_debug_menu_requested, 1);
        }
    }
#if defined(PSX_SDL3)
    return true;
#else
    return 1;
#endif
}

static int macross_debug_menu_signature_valid(void) {
    return psx_mod_read_word(MACROSS_DEBUG_MENU_HOOK) == 0x27BDFFE0u &&
           psx_mod_read_word(MACROSS_DEBUG_MENU_RUNNER) == 0x27BDFFC0u &&
           psx_mod_read_word(MACROSS_DEBUG_MENU_ROOT) == 0x800801D0u &&
           psx_mod_read_word(MACROSS_DEBUG_MENU_ROOT + 4u) == 0x80075880u &&
           psx_mod_read_word(MACROSS_DEBUG_MENU_ROOT + 8u) == 19u;
}

static void macross_debug_menu_hook(CPUState* cpu, uint32_t address) {
    int i;
    (void)address;

    if (macross_debug_menu_phase == MACROSS_DEBUG_MENU_RESUMING) {
        cpu->gpr[31] = macross_debug_menu_resume_gpr[0];
        for (i = 0; i < 4; ++i) {
            cpu->gpr[4 + i] = macross_debug_menu_resume_gpr[1 + i];
        }
        macross_debug_menu_phase = MACROSS_DEBUG_MENU_IDLE;
        SDL_AtomicSet(&macross_debug_menu_active, 0);
        psx_mod_set_rewind_blocked(0);
        psx_mod_set_savestate_blocked(0);
        return;
    }

    if (macross_debug_menu_phase != MACROSS_DEBUG_MENU_IDLE ||
        !SDL_AtomicCAS(&macross_debug_menu_requested, 1, 0) ||
        SDL_AtomicGet(&macross_debug_menu_active)) {
        return;
    }
    if (!SDL_AtomicGet(&macross_debug_menu_verified)) {
        if (!macross_debug_menu_signature_valid()) {
            fprintf(stderr,
                    "Macross VF-X2: retail debug-menu signature mismatch\n");
            psx_mod_counter_add("macross.debug-menu.signature-mismatch", 1u);
            return;
        }
        SDL_AtomicSet(&macross_debug_menu_verified, 1);
    }

    macross_debug_menu_resume_gpr[0] = cpu->gpr[31];
    for (i = 0; i < 4; ++i) {
        macross_debug_menu_resume_gpr[1 + i] = cpu->gpr[4 + i];
    }
    macross_debug_menu_phase = MACROSS_DEBUG_MENU_OPENING;
    SDL_AtomicSet(&macross_debug_menu_active, 1);
    psx_mod_set_rewind_blocked(1);
    psx_mod_set_savestate_blocked(1);
    cpu->gpr[31] = MACROSS_DEBUG_MENU_RUNNER;
    if (!psx_mod_finish_function(cpu)) {
        macross_debug_menu_phase = MACROSS_DEBUG_MENU_IDLE;
        SDL_AtomicSet(&macross_debug_menu_active, 0);
        psx_mod_set_rewind_blocked(0);
        psx_mod_set_savestate_blocked(0);
        fprintf(stderr,
                "Macross VF-X2: unable to redirect to retail debug menu\n");
        return;
    }
    psx_mod_counter_add("macross.debug-menu.opened", 1u);
}

static void macross_debug_menu_runner_hook(CPUState* cpu, uint32_t address) {
    (void)address;
    if (macross_debug_menu_phase != MACROSS_DEBUG_MENU_OPENING) {
        return;
    }

    macross_debug_menu_phase = MACROSS_DEBUG_MENU_RUNNING;
    cpu->gpr[4] = MACROSS_DEBUG_MENU_ROOT;
    cpu->gpr[5] = 0u;
    cpu->gpr[6] = 0u;
    cpu->gpr[7] = 0u;
    cpu->gpr[31] = MACROSS_DEBUG_MENU_RETURN;
}

static void macross_debug_menu_return(CPUState* cpu, uint32_t address) {
    (void)address;
    if (macross_debug_menu_phase != MACROSS_DEBUG_MENU_RUNNING) {
        fprintf(stderr,
                "Macross VF-X2: unexpected retail debug-menu return\n");
        macross_debug_menu_phase = MACROSS_DEBUG_MENU_IDLE;
        SDL_AtomicSet(&macross_debug_menu_active, 0);
        psx_mod_set_rewind_blocked(0);
        psx_mod_set_savestate_blocked(0);
        cpu->gpr[31] = macross_debug_menu_resume_gpr[0];
        return;
    }

    macross_debug_menu_phase = MACROSS_DEBUG_MENU_RESUMING;
    cpu->gpr[31] = MACROSS_DEBUG_MENU_HOOK;
}

static int macross_debug_menu_command(const char* args, char* reply, int cap) {
    const int enabled = SDL_AtomicGet(&macross_debug_menu_enabled);
    const int active = SDL_AtomicGet(&macross_debug_menu_active);
    const int verified = SDL_AtomicGet(&macross_debug_menu_verified);

    if (!enabled) {
        return snprintf(reply, (size_t)cap, "debug-menu package is disabled");
    }
    if (args && !strcmp(args, "status")) {
        return snprintf(reply, (size_t)cap, "enabled=%d active=%d verified=%d",
                        enabled, active, verified);
    }
    if (active) {
        return snprintf(reply, (size_t)cap, "retail debug menu is already active");
    }
    SDL_AtomicSet(&macross_debug_menu_requested, 1);
    return snprintf(reply, (size_t)cap, "retail debug menu queued");
}

static void macross_debug_menu_activate(void) {
    SDL_AtomicSet(&macross_debug_menu_requested, 0);
    SDL_AtomicSet(&macross_debug_menu_enabled, 1);
    SDL_AtomicSet(&macross_debug_menu_active, 0);
    SDL_AtomicSet(&macross_debug_menu_verified, 0);
    macross_debug_menu_phase = MACROSS_DEBUG_MENU_IDLE;
    if (!macross_debug_menu_watch_installed) {
#if defined(PSX_SDL3)
        if (!SDL_AddEventWatch(macross_debug_menu_event_watch, NULL)) {
            fprintf(stderr,
                    "Macross VF-X2: unable to install F12 debug-menu watch: %s\n",
                    SDL_GetError());
            SDL_AtomicSet(&macross_debug_menu_enabled, 0);
            return;
        }
#else
        SDL_AddEventWatch(macross_debug_menu_event_watch, NULL);
#endif
        macross_debug_menu_watch_installed = 1;
    }
}

static void macross_debug_menu_reset(void) {
    if (macross_debug_menu_watch_installed) {
        SDL_DelEventWatch(macross_debug_menu_event_watch, NULL);
        macross_debug_menu_watch_installed = 0;
    }
    SDL_AtomicSet(&macross_debug_menu_requested, 0);
    SDL_AtomicSet(&macross_debug_menu_enabled, 0);
    SDL_AtomicSet(&macross_debug_menu_active, 0);
    SDL_AtomicSet(&macross_debug_menu_verified, 0);
    macross_debug_menu_phase = MACROSS_DEBUG_MENU_IDLE;
    psx_mod_set_rewind_blocked(0);
    psx_mod_set_savestate_blocked(0);
}

static void macross_fast_loading_activate(void) {
    if (!psx_mod_set_load_acceleration(4u, 0u)) {
        fprintf(stderr,
                "Macross VF-X2: unable to enable 4x loading acceleration\n");
    }
}

static void macross_widescreen_activate(void) {
    if (!psx_mod_set_fixed_display_aspect(16u, 9u)) {
        fprintf(stderr,
                "Macross VF-X2: unable to enable native 16:9 output\n");
    }
}

PSX_MOD_CONSTRUCTOR(macross_register_mod_plugins) {
    int debug_menu_registered = 1;

    if (!psx_mod_register_activation_plugin(
            "macross.fast-loading", macross_fast_loading_activate)) {
        fprintf(stderr,
                "Macross VF-X2: unable to register fast-loading plugin\n");
    }
    if (!psx_mod_register_activation_plugin(
            "macross.widescreen.16-9", macross_widescreen_activate)) {
        fprintf(stderr,
                "Macross VF-X2: unable to register widescreen plugin\n");
    }
    debug_menu_registered &= psx_mod_register_activation_plugin(
        "macross.debug-menu", macross_debug_menu_activate);
    debug_menu_registered &= psx_mod_register_session_reset_plugin(
        "macross.debug-menu", macross_debug_menu_reset);
    debug_menu_registered &= psx_mod_register_function_entry_plugin(
        "macross.debug-menu", MACROSS_DEBUG_MENU_HOOK,
        macross_debug_menu_hook);
    debug_menu_registered &= psx_mod_register_function_entry_plugin(
        "macross.debug-menu", MACROSS_DEBUG_MENU_RUNNER,
        macross_debug_menu_runner_hook);
    debug_menu_registered &= psx_mod_register_guest_function_plugin(
        "macross.debug-menu", MACROSS_DEBUG_MENU_RETURN,
        macross_debug_menu_return);
    if (!debug_menu_registered) {
        fprintf(stderr,
                "Macross VF-X2: unable to register retail debug-menu plugin\n");
    }
    if (!psx_mod_register_command(
            "macross.debug-menu", macross_debug_menu_command)) {
        fprintf(stderr,
                "Macross VF-X2: unable to register debug-menu command\n");
    }
}
