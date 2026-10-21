# Kospel PPE4 — Home Assistant integration

A local-polling Home Assistant integration for the **Kospel PPE4** instantaneous
(flow-through) electric water heater, talking directly to its Wi-Fi module over
the LAN. No cloud, no account.

> Reverse-engineered from a live unit (`ppe4_00027514`). The PPE4 Wi-Fi module
> is **not** the same as Kospel's C.MI module (EKCO/EKD boilers) — it speaks a
> different, MODBUS-over-HTTP API. See [docs/protocol.md](docs/protocol.md).

## Features

- **Water heater** entity: outlet temperature + target (working) setpoint.
- **Sensors**: intake (Tin) & outlet (Tout) water temperature, live power draw
  (W), flow rate (l/min), plus derived **energy (kWh)** and **water (l)** totals
  for the Home Assistant Energy dashboard.
- **Active profile** selector (Profile 1–3) and editable **profile presets**.
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
| Water heater – target temp | 1391 | Active working setpoint (÷10 °C) |
| Active profile | 1390 | 0-based index → *Profile 1/2/3* |
| Profile 1/2/3 temperature | 1392 / 1393 / 1394 | Editable presets (÷10 °C) |
| Intake temperature | 1134 | *Tin* (÷10 °C) |
| Outlet temperature | 1135 | *Tout* (÷10 °C) |
| Power | 1138 | Live draw (W) |
| Flow rate | 1139 | ÷10 l/min |
| Energy / Water | derived | Integrated from power/flow (kWh / l) |
| Internal temperature | 1136 | Diagnostic (÷10 °C) |
| Installed / heater power | 1143 / 1144 | W (diagnostic) |

## Status

- **Reading: fully working and validated** against hardware.
- **Writing (setpoint & profile): working and validated** — uses the heater's
  `POST /api/write` endpoint (captured from the official app).
  See [docs/protocol.md](docs/protocol.md#writing).

## Disclaimer

Unofficial. Not affiliated with Kospel. Use at your own risk — it controls a
mains water heater.

## Acknowledgements

- [JanKrl/ha-kospel-cmi](https://github.com/JanKrl/ha-kospel-cmi) and
  [kospel-cmi-lib](https://github.com/JanKrl/kospel-cmi-lib) — for the Kospel
  C.MI boilers. They provided the initial lead that Kospel heaters expose a
  local HTTP API. The PPE4 uses a different (MODBUS-over-HTTP) protocol, so this
  integration shares no code with them, but credit is due for the inspiration.

## License

[MIT](LICENSE)
