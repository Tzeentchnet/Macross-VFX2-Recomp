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
| `.TIX` | 121 | VFX2 VRAM-upload stream using TIM-style rectangles | Confirmed |
| `.TOX` | 60 | Unknown; possibly texture/object companion data | Lead |
| `.MOD` | 57 | VFX2 model container with embedded TMD and optional TIM data | Confirmed |
| `.TMD` | 53 | Standard relative-address PlayStation model data | Confirmed |
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

The 57 `.MOD` files also contain 46 byte-valid standard TIM images. Their
blocks use the normal TIM length and rectangle rules. The self-contained
Variable Fighter files under `MOD/` use these images for all sampled TPage and
CLUT references; smaller mission-specific MOD files can still depend on the
mission TIX bank.

## TIX

TIX is a read-only-decoded VFX2 VRAM-upload stream. It reuses the TIM magic and
TIM image-block rectangle, but its second word is a game-specific pair of
16-bit fields rather than an ordinary TIM flags word.

```text
Offset  Type    Meaning
0x00    u32     Magic, always 0x00000010
0x04    u16     Stream mode: 2 or 4 in the verified files
0x06    u16     Rectangle count for mode 4; zero for mode 2
0x08    ...     Consecutive upload rectangles
```

Each upload rectangle is:

```text
Offset  Type       Meaning
0x00    u32        Complete block length, including this 12-byte header
0x04    u16        VRAM X coordinate in 16-bit words
0x06    u16        VRAM Y coordinate
0x08    u16        Width in 16-bit words
0x0A    u16        Height
0x0C    u16[w*h]   Raw words copied to VRAM
```

For every block in all 121 files:

```text
block_length == 12 + width * height * 2
```

The blocks consume each file exactly, with no footer or trailing padding.

Two stream forms occur:

| Mode | Count field | Files | Interpretation |
|---:|---:|---:|---|
| `2` | `0` | 33 | One direct-color upload; byte-compatible with a no-CLUT 16-bit TIM |
| `4` | `2` through `210`, always even | 88 | Exactly `count` upload rectangles |

Mode-4 rectangles can contain CLUT words, packed 4-bit or 8-bit texels, or
other VRAM data. TIX does not tag the role of an individual rectangle.
Textured TMD primitives provide the TPage and CLUT registers needed to
interpret the uploaded words.

Representative headers remain:

```text
DATA00/BRF/IMGMSN01.TIX
10 00 00 00 04 00 12 00 2C 00 00 00 50 00 FD 01

DATA00/IMAGE020.TIX
10 00 00 00 04 00 D2 00 2C 00 00 00 00 00 FE 01

SYSTEM/ADJUST.TIX
10 00 00 00 04 00 04 00 0C 02 00 00 00 00 E0 01
```

The format is sufficient for a decoder that emulates 1024x512 PS1 VRAM and
resolves TMD texture references. It is not yet sufficient for a safe encoder:
the semantic grouping and intended replacement rules for rectangles remain
unknown, and byte-identical round trips have not been established.

### TMD

All 53 `.TMD` files are standard little-endian PlayStation TMD model data:

```text
Offset  Type  Meaning
0x00    u32   ID, 0x00000041
0x04    u32   Address flags, zero in every disc TMD
0x08    u32   Object count
0x0C    ...   28-byte object descriptors
```

Each object descriptor contains relative offsets and counts for vertices,
normals, and primitives, followed by the signed TMD scale field. When the
address flag is zero, every object offset is relative to the common object
table base at file offset `0x0C`, not to its individual descriptor.

All retail primitives validated as polygon packets in modes `0x20` through
`0x3F`. The observed set covers:

- triangles and quads;
- flat and Gouraud shading;
- lit and no-light packets;
- flat and per-vertex pigment;
- textured and untextured packets;
- one- and two-sided flags; and
- opaque and semitransparent modes.

Textured packets carry normal PS1 CBA/CLUT and TSB/TPage words. Those values
resolve directly against VRAM populated from TIX or TIM upload rectangles.
Vertex and normal records use the standard four signed 16-bit components,
with the fourth component serving as padding.

Quad packet vertices are in GPU triangle-strip order. The two triangles are
`(0, 1, 2)` and `(1, 3, 2)`, giving the conventional mesh perimeter
`(0, 1, 3, 2)`. Treating `(0, 1, 2, 3)` as a perimeter creates crossed
bow-tie faces. In the 7,325 lit quads from the standalone retail TMD files,
the strip-to-perimeter conversion aligned the first geometric triangle with
the stored normal in 7,302 non-degenerate cases (99.7 percent after accounting
for the format's clockwise winding); the raw perimeter interpretation aligned
in only 32 cases.

### MOD

Every `.MOD` file begins with little-endian magic `0x11E1A300`. MOD is a VFX2
container, not tracker music. The 57 files contain 140 fully validated
relative-address TMD blocks and 46 standard TIM images.

The 32-bit word at offset `0x04` is a declared model count. It equals the
number of validated embedded TMD blocks in 54 of 57 files. `MOD/VF01A.MOD`,
`MOD/VF11A.MOD`, and `MOD/VF17.MOD` each contain one additional structurally
valid TMD block beyond that value, so readers should not treat the count as a
safe end-of-file boundary.

The first embedded TMD begins at:

```text
0x1740 + 4 * word_at_MOD_offset_0x20
```

for all 57 verified files. Subsequent TMD and TIM blocks are separated by
game-specific data and alignment, so a reader should validate each candidate
header and all of its relative ranges rather than assuming fixed strides.

The remaining MOD data includes transformation or animation-related records
used by the game, but that envelope is not yet decoded. Static geometry and
embedded textures can be imported without interpreting it.

### Blender companion importer

[Macross VF-X2 Blender](https://github.com/Tzeentchnet/Macross-VFX2-Blender)
is a Blender 5.2 add-on for importing the standalone TMD files and MOD
containers described above. The add-on is maintained separately from the
recompilation project.

## Other formats

The following descriptions are intentionally conservative.

### STR and XA

Two `.STR` files likely contain PlayStation streamed movie data. The single
`.XA` file likely contains XA ADPCM streams. Two additional CUE tracks are CD
audio. Runtime validation confirms XA/SPU behavior on the tested path, but no
stream index has been mapped.

### PAC, TOX, BIN, BGD, CEL, and POS

These are game-specific or insufficiently identified. Treat them as opaque
until both a signature analysis and the relevant guest loader are understood.

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
