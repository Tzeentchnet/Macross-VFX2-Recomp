# Macross VF-X2 technical documentation

This directory records what is currently known about the retail game and this
recompilation project. It is intended for contributors working on
compatibility, localization, asset tooling, or game-specific enhancements.

## Documents

| Document | Contents |
|---|---|
| [Game architecture](architecture.md) | Executable layout, static recompilation pipeline, runtime layers, subsystems, and mod boundaries |
| [Disc and file formats](file-formats.md) | Disc geometry, ISO inventory, known and suspected asset formats, and current TIX findings |
| [Localization](localization.md) | How the English patch works, whether text is stored as images or strings, and simpler future workflows |
| [Cut and disabled content](cut-and-disabled-content.md) | Evidence for dormant debug facilities and a conservative register of possible cut material |

## Evidence labels

The reverse engineering is incomplete. These labels are used throughout:

- **Confirmed**: directly established by configuration, file structure,
  binary signatures, generated code, or runtime observation.
- **Strong inference**: multiple observations support the conclusion, but the
  relevant format or guest routine has not been fully decoded.
- **Lead**: worth investigating, but insufficient to describe as a game
  feature or cut content.
- **Unknown**: the current repository evidence does not answer the question.

Addresses beginning with `0x800...` are guest PlayStation addresses. Plain
hexadecimal offsets such as `0x6F970` are file offsets unless stated
otherwise. Most generated guest functions still have synthetic names such as
`func_8001A154`; a name does not imply that its role has been fully identified.

## Baseline

The documentation describes the verified Japanese release identified in
[the main README](../README.md#legal-disc-required):

- Game ID: `SLPS-02237`
- Executable: `SLPS_022.37`
- Track 1 SHA-256:
  `ba4cd0051cb51705c14401136a29f3364cccab83afb60d24929551a835dd56c1`
- Executable load address and entry PC: `0x80011000`
- Generated guest functions: 2,784 across 34 C shards
- Runtime qualification: boot through the first mission entry, not the full
  campaign

## Reproducibility and legal scope

Original game data, generated disc files, translated image data, and generated
guest C are intentionally not part of the public source tree. Local analysis
paths such as `disc/`, `analysis/`, and `generated/` are evidence produced from
the contributor's own legal disc.

The upstream English patch does not declare a redistribution license. The
project therefore downloads and verifies that patch during local preparation,
creates ignored local overlays, and does not commit its translated pixels.
See [Localization](localization.md) for the exact boundary.

## Current limitations

- Most guest functions do not have semantic names.
- TIX is only partially characterized; there is no checked-in decoder or
  encoder.
- A raw Shift-JIS-looking byte scan is too noisy to prove the presence of a
  usable string table.
- Static call-graph "orphan" status does not prove that code is unreachable.
- No complete campaign trace or asset-use trace exists yet.
- No mission, model, movie, or audio asset is currently confirmed cut.
