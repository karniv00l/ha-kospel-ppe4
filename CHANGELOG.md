# Changelog

All notable changes to this integration are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [Semantic Versioning](https://semver.org/).

## [0.1.3] - 2026-10-24

### Fixed

- **Writes from Home Assistant failed.** The heater rejects any whitespace in
  the JSON body (`status_value` -10, "A character that is not allowed was
  used."), and the integration was sending `{"1390": 1, ...}`. Changing the
  target temperature, the active profile or a profile preset now works.
- **Profiles and target temperature.** Register `1390` is a mode: `0` =
  manual (heat to `1391`), `1`–`3` = Profile 1–3. The previous model treated
  it as a 0-based "highlight" and assumed `1391` was always the target, so HA
  showed the wrong target and profile, and picking "Profile 3" selected
  Profile 2.
  - The water heater's target now reads `1140`, the temperature the heater
    is actually aiming for.
  - Setting a temperature in HA switches the heater to manual at that
    temperature. Saved profiles are not changed.
  - The **Active profile** select now offers *Manual*, *Profile 1*, *Profile 2*
    and *Profile 3*, and writes the same value the official app does.
- **Water usage read 20–25% high** compared with the app. The integration
  estimated it from the flow register, which over-reads.

### Changed

- **Energy** and **Water** now read the heater's own daily counters, the same
  numbers as the app's *Statystyki zużycia*. They're renamed **Energy today**
  and **Water today** and reset at midnight on the heater's clock. Entity IDs
  are unchanged, so Energy dashboard and `utility_meter` setups keep working.
  Right after upgrading, each sensor drops once from the old running total to
  today's value. Home Assistant treats that as a normal reset.

### Documentation

- `docs/protocol.md` documents the daily and monthly usage-counter blocks, the
  manual/profile mode register, the effective target register `1140`, and the
  no-whitespace rule for writes. It also corrects the earlier profile notes.

## [0.1.2] - 2026-10-22

### Added

- Brand icon bundled in `custom_components/kospel_ppe4/brand/`, shown on the
  device and integration pages (Home Assistant 2026.3.0 or newer).

## [0.1.1] - 2026-10-21

First HACS release.

### Added

- Water heater entity: outlet temperature and target temperature.
- Sensors: intake and outlet temperature, live power, flow rate, and energy
  and water totals for the Energy dashboard.
- Active profile select and editable Profile 1–3 presets.
- Diagnostic sensors: internal temperature, installed and heater power.
- Logo, troubleshooting and Energy dashboard docs.

## [0.1.0] - 2026-10-21

Initial version (not released).

[0.1.3]: https://github.com/karniv00l/ha-kospel-ppe4/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/karniv00l/ha-kospel-ppe4/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/karniv00l/ha-kospel-ppe4/releases/tag/v0.1.1
