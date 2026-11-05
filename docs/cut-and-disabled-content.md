# Cut and disabled content

## Scope and confidence

This document records dormant or suspicious material without assuming that
every unused-looking byte is cut content.

Static PlayStation analysis has important blind spots:

- state machines often dispatch through tables;
- function pointers may not appear as ordinary call edges;
- filenames may be formatted dynamically;
- assets can be selected by numeric ID rather than a visible filename;
- retail debug code can remain compiled in but hidden;
- library diagnostics are not necessarily game features.

The current evidence supports retained developer facilities. It does **not**
yet support claims of cut missions, aircraft, movies, models, or audio.

## Summary

| Item | Classification | Original game content? |
|---|---|---|
| Retained configuration/debug menu | Confirmed and restored as an opt-in diagnostic | Yes |
| Test-flight and immortality controls | Confirmed menu entries; behavior not fully qualified | Yes |
| Mission, module, memory, XA, collision, and camera inspectors | Confirmed menu entries; pages not fully qualified | Yes |
| Mission-clear demo diagnostic | Lead; may be normal end-mission code | Yes |
| PS1 graphics diagnostics | Confirmed retained diagnostics | Mostly SDK/library code |
| Analyzer-marked orphan functions | Lead only | Yes |
| Production recomp debug tools disabled | Confirmed project setting | No |
| Native widescreen disabled by default | Confirmed project setting | No |
| Repeated analysis probe directories | Confirmed investigation artifacts | No |
| Cut missions/assets | Not established | Unknown |

## Confirmed: retained debug/configuration menu

The retail executable contains a coherent string block around file offsets
`0x6F970` through `0x6FA1C`. Small representative strings include:

- `Debug Menu`
- `test flight`
- `immortal`
- `Module Config`
- `CONFIGURATION MODE`
- `PAUSE`
- `TARGET`
- `MISSILE`

Nearby formatting strings refer to character, effect, and enemy indices, plus
last-module, mission-state, title, and completion values. The same region
contains selectors for play/demo/clear/failed states, difficulty settings,
aircraft types, and camera modes.

The root descriptor is retained at `0x800801C0`. It points to the
`CONFIGURATION MODE` title, a 19-item pointer array at `0x80075880`, and an
initial selection of zero. The generic menu runner at `0x80025468` is intact,
as are the item descriptors and callbacks.

The default-off **Retail Debug Menu (Experimental)** package verifies those
signatures, then exposes the original root menu on F12. Runtime testing has
confirmed that the retail code renders, accepts directional input, edits
values, exits, resumes the interrupted game function, and can be reopened.
The frame scheduler continues to advance while the menu is active.

**Not yet known:**

- whether an unmodified retail controller sequence reaches the menu;
- whether every individual page functions safely with retail data;
- whether "test flight" is a separate mode or a menu shortcut into normal
  mission code.

## Strong candidate: subsystem inspectors

The debug string block includes coherent labels for:

- module selection;
- mission state and parameters;
- global/used/free memory;
- screen and VRAM state;
- XA;
- collision;
- indicators;
- snapshots and information pages;
- free-angle, free-move, follow-character, follow-effect, and camera modes.

This is more than isolated error text. It suggests one or more developer pages
for inspecting game state and controlling the camera.

These facilities are now available for reverse engineering through the
default-off diagnostic package. Use disposable profiles: changing retail
state through an unqualified page could corrupt progression or trigger
incomplete paths.

## Lead: mission-clear demonstration path

The executable includes the diagnostic:

```text
Failed : Create CMissionClearDemo
```

This shows that a `CMissionClearDemo` concept exists. It does not prove cut
content: the object may implement a normal mission-completion sequence. The
finding becomes meaningful only after its constructor/call sites are mapped
and observed during an ordinary clear.

## Retained SDK and engine diagnostics

The executable contains development-oriented graphics messages, including
graph-debug, graph-reset, display-mask, draw-sync, callback, and invalid
rectangle diagnostics. It also retains an old source-control identification
string for a system source file.

These strings are consistent with PlayStation SDK or engine support compiled
into the retail executable. They are useful landmarks for naming low-level
graphics routines, but should not be described as cut Macross content.

The executable also contains load and error messages for dynamic CD paths,
module loading, and sound-bank size limits. Such diagnostics establish engine
capabilities, not whether a specific asset is unused.

## Weak evidence: analyzer orphan functions

The local analysis classifies many functions as `orphan`, meaning no ordinary
incoming call edge was resolved. Some are also marked `indirect`,
`addr_taken`, or `break`.

An orphan is not dead code. It may be:

- reached through a function-pointer or state table;
- entered by an indirect jump;
- referenced by data the analyzer did not classify;
- called from a root not included in the analysis;
- split at an imperfect function boundary.

Orphan status should only raise priority for a function already associated
with debug strings, an unused table entry, or a runtime-unreached state.

## Media and assets: no confirmed cuts

The disc contains 349 files, including many TIX, TOX, MOD, TMD, PAC, BIN, STR,
XA, and other resources. The current research has not produced a complete
reference graph from executable tables to every file.

Accordingly, none of the following is currently claimed:

- a skipped or removed mission;
- an unused briefing caused by numbering gaps;
- a cut Variable Fighter;
- an unused model or texture;
- an unused movie;
- unused voice or music content.

Dynamic filename patterns and numeric asset IDs make "the filename is not
visible in executable strings" an invalid non-use test.

## Project-disabled features are not original cut content

### Production debug tools

The recompilation's broad host debug tooling is compiled out of the production
runtime. The narrowly scoped, default-off retail-menu package remains
available and is guarded to the supported executable revision. This release
choice is separate from the original game's retained menu code.

### Native widescreen

The project-native 16:9 feature is disabled by default because newly visible
areas expose backdrop voids. It was added by this project and is not a
restored retail feature.

### Analysis probe directories

Local `analysis/probe_*` and widescreen-analysis directories are generated
research outputs. Repeated files in them are not duplicate or unused game
assets.

## How to confirm or reject the leads

### 1. Map the remaining debug callbacks

The root descriptor, runner, item array, and 19 descriptors are mapped.
Continue naming each callback and its data structure before qualifying the
high-risk pages.

### 2. Search for an original retail entry condition

Search callers and state predicates for a retail button sequence, build flag,
save flag, or mission-state requirement. The recomp package's F12 redirect
does not establish that the shipped game had a player-reachable sequence.

### 3. Add runtime reachability counters

Instrument candidate function entries and table dispatch targets. Exercise:

- boot and title idle demos;
- every menu;
- all difficulty levels;
- mission start, failure, and clear paths;
- pause and camera controls.

Absence from one trace is not proof of dead code, but campaign-wide traces can
substantially raise confidence.

### 4. Build an asset-reference index

Parse ISO filenames and executable data tables, then log actual CD file opens
and sector ranges at runtime. Compare the union of campaign traces against the
disc inventory.

### 5. Separate library residue from game systems

Known BIOS, SDK, and engine diagnostics should be named first. Remaining
Macross-specific menu and state code can then be evaluated without inflating
the cut-content list with generic runtime support.

## Current conclusion

The retained developer configuration/debug facility is confirmed and restored
as a default-off diagnostic. Its root menu, test-flight and immortality
controls, mission/module inspection, memory and rendering diagnostics, and
camera entries are intact. No original retail activation sequence has been
found, and the high-risk subpages remain unqualified.

No retail mission, aircraft, model, movie, texture, or audio asset is
currently confirmed cut or disabled.
