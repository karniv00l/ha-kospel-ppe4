<img src="docs/logo/icon.png" width="96" align="right" alt="Kospel PPE4 logo"/>

# Kospel PPE4 — Home Assistant integration

A local-polling Home Assistant integration for the **Kospel PPE4** instantaneous
(flow-through) electric water heater, talking directly to its Wi-Fi module over
the LAN. No cloud, no account.

> Reverse-engineered from a live unit. The PPE4 Wi-Fi module is **not** the same
> as Kospel's C.MI module (EKCO/EKD boilers) — it speaks a different,
> MODBUS-over-HTTP API. See [docs/protocol.md](docs/protocol.md).

> [!WARNING]
> This is an unofficial, community-maintained integration and is not affiliated
> with or endorsed by Kospel. It controls a mains electric water heater — use it
> at your own responsibility.

## Features

- **Water heater** entity: outlet temperature and the temperature the heater
  is aiming for. Setting a temperature switches the heater to manual mode.
- **Sensors**: intake (Tin) & outlet (Tout) water temperature, live power draw
  (W), flow rate (l/min), plus the heater's own daily **energy (kWh)** and
  **water (l)** counters (the same numbers as the app's statistics) for the
  Home Assistant Energy dashboard.
- **Active profile** selector (Manual, Profile 1–3) and editable **profile
  presets**.
- Diagnostic sensors: internal temperature, installed / configured heater power.
- Local polling every 15 s, no authentication required.

## Install (HACS custom repository)

1. HACS → Integrations → ⋮ → *Custom repositories*.
2. Add `https://github.com/karniv00l/ha-kospel-ppe4` as an *Integration*.
3. Install **Kospel PPE4**, restart Home Assistant.
4. Settings → Devices & Services → *Add Integration* → **Kospel PPE4**.
5. Enter the heater's IP (e.g. `192.168.1.36`). A static DHCP lease is
   recommended.

Or copy `custom_components/kospel_ppe4/` into your HA `config/custom_components/`.

## Entities

| Entity | Register(s) | Notes |
|--------|-------------|-------|
| Water heater – current temp | 1135 | Outlet water temp *Tout* (÷10 °C) |
| Water heater – target temp | 1140 | Temperature the heater aims for (÷10 °C); setting it writes 1390 = 0 and 1391 (manual mode) |
| Active profile | 1390 | 0 = *Manual* (uses 1391), 1–3 = *Profile 1/2/3* |
| Profile 1/2/3 temperature | 1392 / 1393 / 1394 | Editable presets (÷10 °C) |
| Intake temperature | 1134 | *Tin* (÷10 °C) |
| Outlet temperature | 1135 | *Tout* (÷10 °C) |
| Power | 1138 | Live draw (W) |
| Flow rate | 1139 | ÷10 l/min |
| Energy today | 1450–1451 | Heater's daily counter, Wh → kWh |
| Water today | 1578–1579 | Heater's daily counter, ÷10 l |
| Internal temperature | 1136 | Diagnostic (÷10 °C) |
| Installed / heater power | 1143 / 1144 | W (diagnostic) |

## Energy & water usage

The **Energy today** (kWh) and **Water today** (l) sensors read the heater's
own daily counters, so they match the app's *Statystyki zużycia* screen. They
reset at midnight (heater clock) and are `total_increasing`, so Home Assistant
treats each reset as a new cycle and keeps the long-term totals.

- **Energy dashboard:** Settings → Dashboards → Energy → *Individual devices* →
  add **Kospel PPE4 Energy**. (Optional: add **Water** under the *Water* source.)
- **Per-day/week/month totals:** add a Utility Meter helper as a **top-level**
  block in `configuration.yaml` (then restart HA — `utility_meter` needs a full
  restart). Verify the source entity IDs first in *Developer Tools → States*
  (filter `kospel_ppe4`):

  ```yaml
  utility_meter:
    ppe4_energy_daily:
      source: sensor.kospel_ppe4_energy
      cycle: daily
    ppe4_energy_monthly:
      source: sensor.kospel_ppe4_energy
      cycle: monthly
    ppe4_water_daily:
      source: sensor.kospel_ppe4_water
      cycle: daily
    ppe4_water_monthly:
      source: sensor.kospel_ppe4_water
      cycle: monthly
  ```

  This creates `sensor.ppe4_energy_daily`, `sensor.ppe4_water_monthly`, etc.

## Status

- **Reading: fully working and validated** against hardware.
- **Writing (setpoint & profile): working and validated** — uses the heater's
  `POST /api/write` endpoint (captured from the official app).
  See [docs/protocol.md](docs/protocol.md#writing).

## Troubleshooting

- **"Failed to connect" when adding the integration** — Home Assistant can't
  reach the heater. From HA's terminal: `curl http://<heater-ip>/api/1140/1`
  should return `"status":"OK"`. Check the IP, and any VLAN/firewall between HA
  and the heater.
- **Heater IP keeps changing** — set a static DHCP lease for it on your router.
- **Entities show "unavailable"** — the module dropped off Wi-Fi; it recovers on
  the next successful poll. Check the heater's Wi-Fi signal icon in the app.
- **No brand icon on the device page** — the icon ships inside the integration
  (`custom_components/kospel_ppe4/brand/`) and needs Home Assistant **2026.3.0
  or newer**; on older versions the icon is simply absent (cosmetic only). See
  [docs/brands.md](docs/brands.md).
- **Enable debug logging** (`configuration.yaml`, then restart):

  ```yaml
  logger:
    logs:
      custom_components.kospel_ppe4: debug
  ```

## Acknowledgements

- [JanKrl/ha-kospel-cmi](https://github.com/JanKrl/ha-kospel-cmi) and
  [kospel-cmi-lib](https://github.com/JanKrl/kospel-cmi-lib) — for the Kospel
  C.MI boilers. They provided the initial lead that Kospel heaters expose a
  local HTTP API. The PPE4 uses a different (MODBUS-over-HTTP) protocol, so this
  integration shares no code with them, but credit is due for the inspiration.

## License

[MIT](LICENSE)
