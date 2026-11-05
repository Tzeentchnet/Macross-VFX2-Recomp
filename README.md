# Macross VF-X2 Recompiled

Work-in-progress static recompilation of **Macross VF-X2 (Japan)** for modern
PCs. This project is based on
[omegakatana92/Macross-VFX-2-Recomp](https://github.com/omegakatana92/Macross-VFX-2-Recomp)
and updated to the current canonical PSXRecomp ecosystem.

The game boots through the BIOS and FMVs, reaches the title and mission
briefing, and enters 3D gameplay. It is not yet a complete-game compatibility
claim.

## Fresh-profile defaults

| Setting | Default | Notes |
|---|---:|---|
| Renderer | Vulkan | OpenGL/software remain fallback paths when needed. |
| Internal Resolution | 4x | Uses the pinned framework package's fresh-profile default. |
| English Localization | On | Generated locally from NXP1000's verified v1.0 release; translates mission briefings and Variable Fighter descriptions. |
| PGXP Precision | On | Geometry correction and perspective-correct texturing are on. CPU propagation and precise culling remain off. |
| Fast Loading | 4x | Fixed title package, on by default. See the qualification note below. |
| Native Widescreen | Off | Experimental native 16:9 rendering; not image stretching. Known backdrop defects prevent enabling it by default. |
| Retail Debug Menu | Off | Original `CONFIGURATION MODE`, exposed as an opt-in diagnostic on F12. |

Existing mod/profile state takes precedence over fresh-profile defaults.

## Pinned upstream revisions

The submodules use the canonical `RetroPortingToolKit` repositories:

| Component | Revision |
|---|---|
| [PSXRecomp](https://github.com/RetroPortingToolKit/psxrecomp) | [`eb6e4be46804538ba54c852429151ecd3e5598db`](https://github.com/RetroPortingToolKit/psxrecomp/commit/eb6e4be46804538ba54c852429151ecd3e5598db) |
| [recomp-ui fork](https://github.com/Tzeentchnet/recomp-ui) | [`72081d93d9337764c67027daada68c09c9a2c0ae`](https://github.com/Tzeentchnet/recomp-ui/commit/72081d93d9337764c67027daada68c09c9a2c0ae) |

The selected PSXRecomp revision is newer than the `v0.3.4-alpha` release and
contains the post-release fixes needed by this project, including setup-host
BIOS validation, split-transfer code generation, widescreen HUD anchoring,
CD/XA readiness behavior, and the current video/PGXP controls. The recomp-ui
fork carries a launcher fix that skips the toolchain page when an already-built
runtime only needs media confirmation.

## Legal disc required

Original game data is not included. Supply your own legally obtained
three-track dump of **Macross VF-X2 (Japan)** (`SLPS-02237`) as one CUE and
three BIN files.

The configured data-track identity is:

- Size: `430867584` bytes
- MD5: `1d54a44b3b7320994cb4ad8cc72b17e6`
- SHA-1: `f7e0d5b2175850b77d5bd8e2efd2123d74240af9`
- SHA-256: `ba4cd0051cb51705c14401136a29f3364cccab83afb60d24929551a835dd56c1`

For the commands below, place the source dump at:

```text
game/
|-- Macross VF-X2 (Japan).cue
|-- Macross VF-X2 (Japan) (Track 1).bin
|-- Macross VF-X2 (Japan) (Track 2).bin
`-- Macross VF-X2 (Japan) (Track 3).bin
```

The generated `disc/` and `generated/` trees are local build inputs and must
not be distributed as source-game content.

## Build requirements

- Git with submodule support
- Python 3.11 or newer
- CMake 3.20 or newer
- Ninja
- A C/C++ toolchain supporting C99, C++17, and C++20
- Vulkan SDK with `glslc` available when building the default Vulkan renderer
- Internet access on the first localized configure, unless the verified
  English xdelta and xdelta3 executable are supplied locally

SDL3 is used by default and is fetched by PSXRecomp when a suitable system
package is unavailable. The tested Windows build used CMake 4.4.4, Ninja
1.13.2, GCC/G++ 16.2.0, Python 3.12, and Vulkan SDK 1.4.363.0.

## Generate and build

Run these commands from PowerShell in the repository root:

```powershell
git submodule update --init --recursive

python .\psxrecomp\psxrecomp_cli.py generate `
    --config .\game.toml `
    --project-root . `
    --disc ".\game\Macross VF-X2 (Japan).cue"

cmake -S . -B .\build-release -G Ninja `
    -DCMAKE_BUILD_TYPE=Release `
    -DPSX_DEBUG_TOOLS=OFF

cmake --build .\build-release --target psx-runtime --parallel
```

The generation command verifies and prepares the disc, generates OpenBIOS and
the game C sources, and builds the required emitters if they are missing.
The following CMake configure also downloads and verifies the official
NXP1000 v1.0 English patch, applies it only to a temporary copy, and generates
a native PSXRecomp overlay package under the ignored local mod directory.

Alternatively, configure and build before generation, launch
`build-release\Macross_VF_X2_Recompiled.exe`, and use the recomp-ui first-run
wizard. A source tree without generated game C builds a setup host that can
select the legal disc, generate the project, and rebuild the playable runtime.

Run the finished build with:

```powershell
& ".\build-release\Macross_VF_X2_Recompiled.exe" `
    --disc ".\disc\Macross VF-X2 (Japan).cue"
```

## Enhancement status

### English localization

The default-on **English Localization** mod uses
[NXP1000/Macross-VFX2-English](https://github.com/NXP1000/Macross-VFX2-English)
v1.0. It translates mission briefing graphics, descriptions for the Variable
Fighters, and related interface text. Translation credits from the upstream
project are PixelatedShinobi, daburuwosagase, and getterdrill; NXP1000
published the xdelta release.

The upstream repository does not currently declare a redistribution license,
so neither its xdelta nor translated game assets are committed here. During a
local configure, [the preparation tool](tools/prepare_english_localization.py):

1. verifies the stock raw Track 1 SHA-256;
2. downloads the exact upstream v1.0 xdelta and verifies
   `e26291021c82e49a4c7e429c82fa729775ba6311df757e6355a28335c7caa66a`;
3. downloads a pinned Apache-2.0 xdelta3 build, unless one was supplied;
4. verifies the patched Track 1 result and its expected 310 changed sectors;
5. converts those changes into hash-guarded `disc_user` overlays; and
6. deletes the temporary patched disc.

Only the ignored local package and build output contain the generated overlay
payloads. Do not commit them or include them in a public release without
permission from the upstream patch authors. Clean setup-host builds contain
the importer but no patch or translated assets; players generate those from
their own legal disc during setup.

For an offline configure, provide the exact upstream patch and a local xdelta3
with LZMA support:

```powershell
cmake -S . -B .\build-release -G Ninja `
    -DMACROSS_ENGLISH_PATCH="C:\path\Macross_VFX2_ENG.xdelta" `
    -DMACROSS_XDELTA3_EXECUTABLE="C:\path\xdelta3.exe"
```

Set `-DMACROSS_ENABLE_ENGLISH_LOCALIZATION=OFF` to omit the package entirely.
Once generated, players can still disable **English Localization** in Mods;
existing profile state takes precedence over its fresh-profile default.

### Vulkan and 4x Internal Resolution

Vulkan is compiled and requested by default. Runtime telemetry has confirmed
the Vulkan backend and an effective 4x internal scale (960 internal reference
lines for a 240-line gameplay mode).

### PGXP Precision

The primary executable is built with PSXRecomp's PGXP hook flavor. The bundled
title override enables per-vertex geometry correction and perspective-correct
texturing on fresh profiles. CPU-mode propagation and precise culling stay off
because those options alter guest-visible behavior and have not been qualified
for this title.

### Fast Loading (4x)

The title package selects fixed 4x host pacing for PSXRecomp's sustained
non-XA loading detector. It does not shorten guest-visible CD deadlines or
remove VBlanks, interrupts, callbacks, XA, or FMV cadence.

Validation has covered boot FMVs, title/menu transitions, mission briefing,
fighter selection, and loading into the first 3D mission. XA audio was
delivered and the CD/SPU telemetry reported no CD overflow or underflow during
that run. The complete campaign and every loading/audio path have not been
qualified, so disable **Fast Loading (4x)** if a transition, FMV, or audio
regression appears.

The deprecated generic PSXRecomp CD Speed and Fast Loading packages are
excluded. This project uses its own package ID because current upstream release
policy does not accept those generic packages as title-verified loaders.

### Retail debug menu

The retail executable still contains its original 19-entry
`CONFIGURATION MODE`. To use it, enable **Retail Debug Menu (Experimental)**
under **Mods > Diagnostics**, start the game, and press **F12**. The menu uses
the configured player-one controls: the D-pad moves between entries and edits
values, while Start exits.

The package redirects guest control flow instead of running the menu in a
nested host call. Normal scheduling and input sampling therefore continue
while the original menu loop runs. Save states and Rewind are temporarily
blocked until the menu exits because the redirect carries host-side resume
state.

Opening, navigation, option editing, exit, and repeated use have been tested.
The individual test-flight, mission, module, memory, XA, collision, camera,
and state-editing pages have not. Use a disposable profile: these are retained
developer controls and can disrupt progression or saves. The feature remains
disabled by default.

### Native widescreen investigation

The optional **Native Widescreen (Experimental)** mod selects a real 16:9
render surface. In 320x240 gameplay it produces a 426x240 native-wide surface
(1704x960 at 4x), reveals additional horizontal field of view, renders 3D
models into the side margins, and keeps the HUD anchored. It does not stretch
the original 4:3 image.

It is intentionally disabled by default. Live first-mission testing found
large black voids and seams in the planet/city backdrop where finite background
geometry does not cover the newly visible area. Static analysis also found no
safe Macross-specific culling sites to patch. Menus and FMVs remain on the 4:3
presentation path, but gameplay needs title-specific backdrop and possibly
culling fixes before native widescreen can be considered production-ready.

## Validation summary

- Clean setup-host configure/build: passed
- Full game generation: 2,784 functions across 34 generated C shards
- Production Release runtime build with debug tools disabled: passed
- Vulkan initialization and 4x internal resolution: passed
- English localization import, 36 overlay guards, and runtime resolution:
  passed
- English mission briefing rendering: passed
- PGXP activation in 3D gameplay: passed
- Boot, FMVs, title, briefing, fighter selection, and first mission entry:
  passed
- First-mission XA/SPU playback under Fast Loading 4x: passed
- Native 16:9 surface and extra horizontal field of view: confirmed
- Native 16:9 backdrop coverage: failed; feature remains experimental/off
- Retail F12 menu activation, navigation, editing, exit, and repeated use:
  passed; diagnostic subpages remain unqualified

There are currently no project CTest cases. Runtime qualification beyond the
first mission is still required.

## Technical documentation

Reverse-engineering notes are maintained under [docs/](docs/README.md):

- [Game architecture](docs/architecture.md)
- [Disc and file formats](docs/file-formats.md)
- [Localization architecture and options](docs/localization.md)
- [Cut and disabled content](docs/cut-and-disabled-content.md)

The documentation distinguishes confirmed behavior from inferences and weak
leads. In particular, the current English translation changes rasterized TIX
image resources rather than a conventional text string table, and no mission
or media asset is currently confirmed cut.

## Companion tooling

[Macross VF-X2 Blender](https://github.com/Tzeentchnet/Macross-VFX2-Blender)
is a companion Blender 5.2 add-on for importing the game's standalone TMD
models and MOD model containers. It implements the asset-format findings
documented in [Disc and file formats](docs/file-formats.md).

## Project layout

```text
.
|-- CMakeLists.txt
|-- game.toml
|-- codegen_setup.c / codegen_setup.h
|-- docs/
|-- mods/preloaded/
|-- src/macross_mods.c
|-- tools/prepare_english_localization.py
|-- seeds/
|-- psxrecomp/          # pinned framework submodule
|-- recomp-ui/          # pinned launcher UI submodule
|-- game/               # local source dump; ignored
|-- disc/               # prepared local disc; ignored
`-- generated/          # generated game C; ignored
```

## License and credits

Project source is licensed under the [GNU General Public License v3.0](LICENSE).
PSXRecomp, recomp-ui, and their dependencies retain their own licenses.

Thanks to:

- [omegakatana92/Macross-VFX-2-Recomp](https://github.com/omegakatana92/Macross-VFX-2-Recomp)
  for the original project base
- [RetroPortingToolKit/psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp)
- [RetroPortingToolKit/recomp-ui](https://github.com/RetroPortingToolKit/recomp-ui)

Macross VF-X2, its characters, names, artwork, music, trademarks, and other
intellectual property remain the property of their respective rights holders.
This independent fan project is not affiliated with or endorsed by them and
does not distribute original game data.
