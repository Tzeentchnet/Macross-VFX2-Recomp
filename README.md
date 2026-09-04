# Macross VF-X2 (Japan) - Recomp


First release of the Macross VF-X2 recompilation project.

## Status
- Graphics: Working
- Gameplay: Working
- Performance: Working
- Tested successfully in-game

## Included
- Windows executable

## Requirements
- A legally obtained copy of Macross VF-X2 is required.
- Original game data is not included.

## Credits
Built using PSXRecomp and recomp-ui.

Upload:



> **Work in Progress:** This recompilation project is currently under development. Features, compatibility, performance, and functionality may change as development continues.

A modern fan-made recompilation project for **Macross VF-X2 (Japan)**, originally released for the **Sony PlayStation**.

## Built With PSXRecomp

This project is built using [PSXRecomp](https://github.com/mstan/psxrecomp), the PlayStation 1 static recompiler framework created by mstan. The framework is included in this project as a Git submodule. The shared Dear ImGui launcher comes from the [recomp-ui](https://github.com/mstan/recomp-ui) submodule.

## Layout (New Project Layout)

This project follows the mstan **New Project Layout** (root-level `psxrecomp/` + `recomp-ui/` submodules, thin project-level `CMakeLists.txt`, `game.toml`, `seeds/`, `codegen_setup.c/.h`).

```
MacrossVFX2Recomp/
├── CMakeLists.txt           # thin: psxrecomp_add_game_runtime(...)
├── game.toml                # identity, EXE header, disc digests, netplay gates
├── codegen_setup.c / .h     # title config for the recomp-ui wizard
├── seeds/
│   └── ghidra_funcs.txt     # first-pass boot-EXE JAL seeds
├── assets/                  # staged icon (psxrecomp.ico/.png/.svg)
├── disc/                    # local disc working tree (gitignored)
├── psxrecomp/               # framework submodule
├── recomp-ui/               # launcher UI submodule
├── generated/               # local C output (gitignored, regenerated)
└── .gitignore
```

## Disc Required

This project **does not include the original game disc image or copyrighted assets**.

To play, you must provide your **own legally obtained copy** of *Macross VF-X2 (Japan)*.

The original game disc image must **not** be uploaded to this repository or included with releases.

## Build / Generate

The first run of the launcher will use the recomp-ui **first-run setup wizard** + **Generate & rebuild** to:

1. Read your legal disc with the local `psxrecomp_cli.py`
2. Generate `OpenBIOS` and the game C into `generated/`
3. CMake configure + build the playable runtime

End users (or RetComM) can do this end-to-end; the source repo ships a setup-host exe that forwards to the playable build.

To build manually:

```bash
cmake -S . -B build-release -G Ninja \
    -DCMAKE_C_COMPILER=C:/msys64/mingw64/bin/gcc.exe \
    -DCMAKE_CXX_COMPILER=C:/msys64/mingw64/bin/g++.exe \
    -DPSX_SDL_BACKEND=SDL2
cmake --build build-release --target psx-runtime -j
```

## Copyright

**Macross VF-X2 (Japan)**, its characters, names, artwork, music, trademarks, and other intellectual property remain the property of their respective copyright and trademark holders.

This is an independent fan-made recompilation project.

No original game disc images or copyrighted game assets are distributed with this project.

**All rights to the original game and its associated intellectual property remain with their respective owners.**

## Disclaimer

This project is an independent fan-made recompilation and is **not affiliated with or endorsed by the original game's rights holders**.
