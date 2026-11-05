# Macross VF-X2 bundled mods

These packages are staged after the framework catalog. The PGXP package uses
the framework package ID and version intentionally so this title can change its
fresh-profile default without changing the shared implementation.

- English Localization is generated locally from NXP1000's verified v1.0
  xdelta release and the player's legal stock Track 1, then enabled by default.
  The upstream patch and generated translated assets are intentionally absent
  from source control. Clean setup-host builds contain neither.
- PGXP Precision is enabled by default with CPU propagation and precise culling
  left off.
- Macross Fast Loading applies fixed 4x host pacing. It remains experimental
  until the title's complete loading and audio paths are qualified. Boot,
  FMVs, XA audio, and the first mission transition have been exercised without
  CD buffer errors.
- Native Widescreen exposes the framework's non-stretched 16:9 render path as
  an experimental, default-off feature. It renders a genuinely wider surface,
  but first-mission testing exposes large black voids and seams in the
  planet/city backdrop. Static analysis has not identified trustworthy
  Macross-specific background or culling hooks to correct them.
- Retail Debug Menu exposes the dormant original CONFIGURATION MODE on F12.
  It is disabled by default because its test-flight, immortality, mission,
  module, memory, XA, collision, and camera controls can change live game
  state. Opening, navigation, option editing, exit, and repeated use have been
  qualified; the individual diagnostic pages have not.

Existing player settings take precedence over these fresh-profile defaults.
