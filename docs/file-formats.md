# Disc and file formats

## Disc layout

The verified release uses:

| Track | CUE mode | Size | Purpose |
|---|---|---:|---|
| 1 | `MODE2/2352` | 430,867,584 bytes | ISO 9660 data track |
| 2 | `AUDIO` | 47,451,600 bytes | CD audio |
| 3 | `AUDIO` | 37,573,200 bytes | CD audio |

`SYSTEM.CNF` boots `SLPS_022.37;1`. The executable begins with the standard
`PS-X EXE` signature and is 475,136 bytes.

### Raw data-sector geometry

The localization importer uses the Mode 2 Form 1 layout:

| Region | Raw-sector offset | Size |
|---|---:|---:|
| Sync, header, and subheader | `0` | 24 bytes |
| ISO user data | `24` | 2,048 bytes |
| EDC/ECC tail | `2,072` | 280 bytes |
| Complete raw sector | `0` | 2,352 bytes |

PSXRecomp `disc_user` overlays address the logical 2,048-byte user-data
stream. The project therefore does not need to distribute or reproduce raw
sector parity bytes.

## ISO inventory

The verified Track 1 contains 349 files:

| Extension | Count | Current interpretation | Confidence |
|---|---:|---|---|
| `.TIX` | 121 | Game-specific image or image-container resource | Strong inference |
| `.TOX` | 60 | Unknown; possibly texture/object companion data | Lead |
| `.MOD` | 57 | Game-specific module/model data; not assumed to be tracker music | Lead |
| `.TMD` | 53 | Likely PlayStation model data | Strong inference |
| `.PAC` | 19 | Likely package/archive container | Lead |
| `.BIN` | 19 | Opaque game data or banks | Unknown |
| `.BGD` | 5 | Likely background data | Lead |
| `.CEL` | 4 | Likely cell/animation data | Lead |
| `.POS` | 3 | Likely position/path data | Lead |
| `.TIM` | 3 | Standard PlayStation image resources | Confirmed |
| `.STR` | 2 | Likely PlayStation streamed movie data | Strong inference |
| `.XA` | 1 | Likely XA ADPCM data | Strong inference |
| `.37` | 1 | `SLPS_022.37` executable | Confirmed |
| `.CNF` | 1 | `SYSTEM.CNF` boot configuration | Confirmed |

Extension names are not enough to prove a format. Entries marked as leads
must be checked by signature and by the guest loader before implementing
tools.

## PS-X EXE

`SLPS_022.37` uses the normal PlayStation executable container:

```text
50 53 2D 58 20 45 58 45
P  S  -  X     E  X  E
```

The configured load address and entry PC are both `0x80011000`. See
[Game architecture](architecture.md#executable-and-memory-layout).

## TIM

The three `.TIM` files begin with standard PlayStation TIM magic:

```text
10 00 00 00
```

Representative resources:

| Path | Size | Flags word |
|---|---:|---|
| `DATA99/IMAGE990.TIM` | 65,824 bytes | `0x00000009` |
| `DATA99/IMAGE991.TIM` | 65,824 bytes | `0x00000009` |
| `DATA99/IMAGE992.TIM` | 4,160 bytes | `0x00000008` |

TIM flags describe indexed/direct pixel mode and CLUT presence. These files
can be approached with existing PlayStation TIM tooling, subject to normal
palette and transparency handling.

## TIX

### Confirmed observations

- All 121 files begin with `10 00 00 00`.
- The second 32-bit word does not behave like a conventional TIM flags word.
- TIX sizes range from roughly 11 KiB to 460 KiB in the inspected image.
- Mission briefings and several interface/description resources are TIX.
- The English patch changes only TIX files.
- No complete TIX decoder or encoder exists in this repository.

Representative headers:

```text
DATA00/BRF/IMGMSN01.TIX
10 00 00 00 04 00 12 00 2C 00 00 00 50 00 FD 01

DATA00/IMAGE020.TIX
10 00 00 00 04 00 D2 00 2C 00 00 00 00 00 FE 01

SYSTEM/ADJUST.TIX
10 00 00 00 04 00 04 00 0C 02 00 00 00 00 E0 01
```

The shared `0x00000010` first word is image-like and matches TIM magic, but a
TIX file must not be passed to a TIM decoder as if it were one ordinary TIM.
For example, `04 00 12 00` would be `0x00120004` as a TIM flags word, which is
not a normal standalone TIM mode. TIX is likely a wrapper, collection, or
related game-specific structure.

### Strong inferences

The localized files behave like indexed raster resources:

- Replacing their contents changes visible briefing and description text.
- No executable or conventional text-table file is changed.
- The changed-byte volume is consistent with pixel/tile replacement.
- Header fields vary in ways compatible with image dimensions, placement,
  record counts, palette data, or VRAM coordinates.

A plausible working model is:

```text
TIX
|-- container or record metadata
|-- one or more image/tile records
|-- CLUT/palette data
`-- indexed pixel data
```

This model is not yet sufficient to write a safe encoder.

### Unknowns

- Header schema and endianness of each field beyond the fixed first word
- Record count and record boundaries
- 4-bit versus 8-bit indexed modes
- CLUT location and BGR555 interpretation
- Pixel swizzling or tile order
- Compression, if any
- Alignment and padding rules
- Whether TOX files describe or reference TIX records

### Recommended TIX research sequence

1. Build a read-only header dumper for all 121 files and cluster the second
   through eighth words by value.
2. Search for nested valid TIM block structures, not just `0x10` byte
   patterns.
3. Locate plausible BGR555 CLUTs and render adjacent data as 4-bit and 8-bit
   indexed pixels.
4. Compare stock and locally patched versions of the same TIX at byte and
   tile granularity.
5. Validate candidate decoding against runtime screenshots.
6. Only after round-trip identity is achieved, implement an encoder.

## Other formats

The following descriptions are intentionally conservative.

### TMD

The `.TMD` extension is conventionally used for PlayStation 3D model data.
The disc contains 53 such files, making model use likely, but the headers and
guest loader have not yet been documented here.

### STR and XA

Two `.STR` files likely contain PlayStation streamed movie data. The single
`.XA` file likely contains XA ADPCM streams. Two additional CUE tracks are CD
audio. Runtime validation confirms XA/SPU behavior on the tested path, but no
stream index has been mapped.

### PAC, MOD, TOX, BIN, BGD, CEL, and POS

These are game-specific or insufficiently identified. Treat them as opaque
until both a signature analysis and the relevant guest loader are understood.
In particular, `.MOD` must not be assumed to mean Amiga tracker music.

## English-patch footprint

The verified upstream patch changes 15 files:

```text
DATA00/BRF/IMGMSN01.TIX
DATA00/BRF/IMGMSN02.TIX
DATA00/BRF/IMGMSN03.TIX
DATA00/BRF/IMGMSN04.TIX
DATA00/BRF/IMGMSN05.TIX
DATA00/BRF/IMGMSN07.TIX
DATA00/BRF/IMGMSN08.TIX
DATA00/BRF/IMGMSN09.TIX
DATA00/BRF/IMGMSN10.TIX
DATA00/BRF/IMGMSN11.TIX
DATA00/BRF/IMGMSN12.TIX
DATA00/BRF/IMGMSN14.TIX
DATA00/IMAGE020.TIX
DATA00/IMAGE040.TIX
SYSTEM/ADJUST.TIX
```

The first twelve are mission briefing resources. The remaining three contain
description or related interface imagery.

The patch changes:

- 310 Mode 2 Form 1 sectors
- 221,336 user-data bytes
- no raw-sector headers
- no executable bytes
- no standalone TIM files
- no ISO directory records

The local importer groups the result into 36 contiguous guarded overlays.
Those overlays contain 634,880 bytes because complete 2,048-byte logical
sectors are stored for every covered range.

See [Localization](localization.md) for the consequences of this footprint.
