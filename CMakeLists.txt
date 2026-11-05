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

set(PSX_RECOMP_UI ON CACHE BOOL
    "Build the shared recomp-ui Dear ImGui launcher" FORCE)
set(PSX_SETUP_WIZARD ON CACHE BOOL
    "Advertise first-run setup wizard + Generate & rebuild in recomp-ui" FORCE)
set(PSX_ENABLE_VULKAN ON CACHE BOOL
    "Build the Vulkan renderer when the SDK is available" FORCE)

include("${PSXRECOMP_ROOT}/runtime/runtime.cmake")

option(MACROSS_ENABLE_ENGLISH_LOCALIZATION
    "Generate the default-on English localization mod from NXP1000 v1.0" ON)
set(MACROSS_ENGLISH_PATCH "" CACHE FILEPATH
    "Optional local Macross_VFX2_ENG.xdelta v1.0 (otherwise downloaded)")
set(MACROSS_XDELTA3_EXECUTABLE "" CACHE FILEPATH
    "Optional local xdelta3 executable with LZMA support")

set(MACROSS_MOD_PACKAGES_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/mods/preloaded/packages")
set(MACROSS_ENGLISH_TOOL
    "${CMAKE_CURRENT_SOURCE_DIR}/tools/prepare_english_localization.py")
set(MACROSS_ENGLISH_PACKAGE_DIR
    "${MACROSS_MOD_PACKAGES_DIR}/macross.localization.english")
set(MACROSS_PREPARED_TRACK
    "${CMAKE_CURRENT_SOURCE_DIR}/disc/Macross VF-X2 (Japan) (Track 1).bin")
set(MACROSS_SOURCE_TRACK
    "${CMAKE_CURRENT_SOURCE_DIR}/game/Macross VF-X2 (Japan) (Track 1).bin")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${MACROSS_ENGLISH_TOOL}"
    "${MACROSS_PREPARED_TRACK}"
    "${MACROSS_SOURCE_TRACK}")

if(MACROSS_ENABLE_ENGLISH_LOCALIZATION)
    find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
    if(EXISTS "${MACROSS_PREPARED_TRACK}")
        set(_MACROSS_ENGLISH_SOURCE "${MACROSS_PREPARED_TRACK}")
    elseif(EXISTS "${MACROSS_SOURCE_TRACK}")
        set(_MACROSS_ENGLISH_SOURCE "${MACROSS_SOURCE_TRACK}")
    else()
        set(_MACROSS_ENGLISH_SOURCE "")
    endif()

    if(_MACROSS_ENGLISH_SOURCE)
        set(_MACROSS_ENGLISH_COMMAND
            "${Python3_EXECUTABLE}" "${MACROSS_ENGLISH_TOOL}"
            --source-track "${_MACROSS_ENGLISH_SOURCE}"
            --packages-dir "${MACROSS_MOD_PACKAGES_DIR}")
        if(MACROSS_ENGLISH_PATCH)
            list(APPEND _MACROSS_ENGLISH_COMMAND
                --patch "${MACROSS_ENGLISH_PATCH}")
        endif()
        if(MACROSS_XDELTA3_EXECUTABLE)
            list(APPEND _MACROSS_ENGLISH_COMMAND
                --xdelta3 "${MACROSS_XDELTA3_EXECUTABLE}")
        endif()
        execute_process(
            COMMAND ${_MACROSS_ENGLISH_COMMAND}
            RESULT_VARIABLE _MACROSS_ENGLISH_RESULT
            OUTPUT_VARIABLE _MACROSS_ENGLISH_STDOUT
            ERROR_VARIABLE _MACROSS_ENGLISH_STDERR
            OUTPUT_STRIP_TRAILING_WHITESPACE
            ERROR_STRIP_TRAILING_WHITESPACE)
        if(NOT _MACROSS_ENGLISH_RESULT EQUAL 0)
            message(FATAL_ERROR
                "Unable to prepare the English localization mod.\n"
                "${_MACROSS_ENGLISH_STDOUT}\n${_MACROSS_ENGLISH_STDERR}\n"
                "Provide the verified patch with "
                "-DMACROSS_ENGLISH_PATCH=<path>, or opt out with "
                "-DMACROSS_ENABLE_ENGLISH_LOCALIZATION=OFF.")
        endif()
        message(STATUS "${_MACROSS_ENGLISH_STDOUT}")
    else()
        execute_process(
            COMMAND "${Python3_EXECUTABLE}" "${MACROSS_ENGLISH_TOOL}"
                --packages-dir "${MACROSS_MOD_PACKAGES_DIR}" --clean
            RESULT_VARIABLE _MACROSS_ENGLISH_CLEAN_RESULT
            OUTPUT_QUIET
            ERROR_VARIABLE _MACROSS_ENGLISH_CLEAN_STDERR
            ERROR_STRIP_TRAILING_WHITESPACE)
        if(NOT _MACROSS_ENGLISH_CLEAN_RESULT EQUAL 0)
            message(FATAL_ERROR
                "Unable to clear the generated English localization package: "
                "${_MACROSS_ENGLISH_CLEAN_STDERR}")
        endif()
        message(STATUS
            "Macross English localization will be generated after the legal "
            "Track 1 image is prepared")
    endif()
elseif(EXISTS "${MACROSS_ENGLISH_PACKAGE_DIR}")
    find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${MACROSS_ENGLISH_TOOL}"
            --packages-dir "${MACROSS_MOD_PACKAGES_DIR}" --clean
        RESULT_VARIABLE _MACROSS_ENGLISH_CLEAN_RESULT
        OUTPUT_QUIET
        ERROR_VARIABLE _MACROSS_ENGLISH_CLEAN_STDERR
        ERROR_STRIP_TRAILING_WHITESPACE)
    if(NOT _MACROSS_ENGLISH_CLEAN_RESULT EQUAL 0)
        message(FATAL_ERROR
            "Unable to clear the generated English localization package: "
            "${_MACROSS_ENGLISH_CLEAN_STDERR}")
    endif()
endif()

set(PSX_PRELOADED_MODS "${CMAKE_CURRENT_SOURCE_DIR}/mods/preloaded")
if(NOT IS_DIRECTORY "${PSX_PRELOADED_MODS}")
    set(PSX_PRELOADED_MODS "NONE")
endif()

psxrecomp_add_game_runtime(psx-runtime
    PRELOADED_MODS_DIR "${PSX_PRELOADED_MODS}"
    ENABLE_SETUP_WIZARD
    PGXP
    EXE_NAME "Macross_VF_X2_Recompiled"
    WINDOW_TITLE "Macross VF-X2 Recompiled"
    DEFAULT_GAME_CONFIG_PATH "game.toml"
    MAX_PLAYERS 1
    GEN_MARKER "generated/SLPS_022.37_dispatch.c"
    GEN_FULL_GLOB "generated/SLPS_022.37_full_*.c"
    CODEGEN_SETUP_SOURCES codegen_setup.c
    EXCLUDE_BUILTIN_MODS
        psx.enhancement.cd-speed
        psx.enhancement.fast-loading
)

target_sources(psx-runtime PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/src/macross_mods.c")

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
