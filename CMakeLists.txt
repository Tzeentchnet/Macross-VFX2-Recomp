cmake_minimum_required(VERSION 3.20)
set(PSXRECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/psxrecomp" CACHE PATH
    "Path to psxrecomp")
if(NOT EXISTS "${PSXRECOMP_ROOT}/runtime/runtime.cmake")
    message(FATAL_ERROR
        "PSXRecomp runtime is missing: ${PSXRECOMP_ROOT}/runtime/runtime.cmake\n"
        "This project expects the psxrecomp framework checkout at ${PSXRECOMP_ROOT}.\n"
        "Run: git submodule update --init --recursive\n"
        "If psxrecomp/ is not a submodule, set -DPSXRECOMP_ROOT=<path-to-psxrecomp>.")
endif()

project(MacrossVFX2Recomp LANGUAGES C CXX)

# --- Opt-in product surfaces (OFF by default in the framework) -------------
# Enable the shared recomp-ui Dear ImGui launcher (lives in the
# recomp-ui submodule at the repo root). The new mstan layout uses
# PSX_RECOMP_UI for this; PSX_LAUNCHER is the historical alias and is
# not recognised in the current framework.
set(PSX_RECOMP_UI ON CACHE BOOL
    "Build the shared recomp-ui Dear ImGui launcher" FORCE)

# First-run setup wizard + Generate & rebuild (recomp-ui). This is what
# the user means by "the updated recomp-ui launcher" -- a setup-host
# exe that lets end users Generate the game C from a legal disc.
set(PSX_SETUP_WIZARD ON CACHE BOOL
    "Advertise first-run setup wizard + Generate & rebuild in recomp-ui" FORCE)

# Prefer the SDL2 backend (MinGW builds have shipped SDL2 via MSYS2;
# the SDL3 default needs a newer toolchain). The runtime CMake gates
# both options, so this is the only project-side knob to flip.
set(PSX_SDL_BACKEND "SDL2" CACHE STRING "SDL backend (SDL3 or SDL2)" FORCE)

include("${PSXRECOMP_ROOT}/runtime/runtime.cmake")

# This project's own mod catalog. The framework stages it -- together
# with its builtin psx.* packages -- into <exe-dir>/mods/bundled, and
# refuses to configure if a catalog exists here but is not declared.
set(PSX_PRELOADED_MODS "${CMAKE_CURRENT_SOURCE_DIR}/mods/preloaded")
if(NOT IS_DIRECTORY "${PSX_PRELOADED_MODS}")
    set(PSX_PRELOADED_MODS "NONE")
endif()

psxrecomp_add_game_runtime(psx-runtime
    PRELOADED_MODS_DIR "${PSX_PRELOADED_MODS}"
    ENABLE_SETUP_WIZARD
    WINDOW_TITLE "Macross VF-X2 Recompiled"
    DEFAULT_GAME_CONFIG_PATH "game.toml"
    MAX_PLAYERS 1
    GEN_MARKER "generated/SLPS_022.37_dispatch.c"
    GEN_FULL_GLOB "generated/SLPS_022.37_full_*.c"
    CODEGEN_SETUP_SOURCES codegen_setup.c
)

# Stage runtime configs next to the exe for direct build/ launches.
foreach(_PSX_RUNTIME_CONFIG game.toml game_options.toml)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${_PSX_RUNTIME_CONFIG}")
        add_custom_command(TARGET psx-runtime POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${CMAKE_CURRENT_SOURCE_DIR}/${_PSX_RUNTIME_CONFIG}"
                "$<TARGET_FILE_DIR:psx-runtime>/${_PSX_RUNTIME_CONFIG}"
            COMMENT "Staging ${_PSX_RUNTIME_CONFIG}"
            VERBATIM)
    endif()
endforeach()
