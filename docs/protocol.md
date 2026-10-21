# Kospel PPE4 Wi-Fi module — protocol notes

Reverse-engineered from a live PPE4 (`ppe4_000XXXXX`, firmware served the
"KOSPEL PPE4 Wi-Fi configuration" page at `/`).

## Transport

- Plain HTTP, port 80, **no authentication**.
- The module is an ESP32-class device joined to the home Wi-Fi (the root page
  also offers an AP-scan / join flow via `GET`/`POST /api/ap`).

## Reading registers

```
GET http://<host>/api/<start>/<count>
```

- `<start>` — decimal MODBUS start address.
- `<count>` — number of 16-bit registers (max ~48 per request).

Response:

```json
{"ver":"1.0","status":"OK","status_value":"0",
 "res":{"1140":420,"1141":0, ...}}
```

Quirks:

- Values are **unsigned 16-bit decimals**. Temperatures are deci-degrees
  (`420` → `42.0 °C`).
- Signed-looking values use two's complement (`65516` → `-20`).
- `0xFFFF` (65535) and `0xAAAA` (43690) are "unused / no sensor" markers.
- A read that hits an empty region returns **invalid JSON**: `..."res":}}`.
  Parse defensively (treat as empty).
- Errors come back as `status: "ERROR"` with messages like
  `Wrong MODBUS start address.` (non-numeric path) or
  `Wrong MODBUS register count.` (count too large).

### Register map (observed)

Confirmed against the app's **Parametry** (parameters) screen and by watching
registers while hot water flowed:

| Addr | App label | Meaning | Scale | Confidence |
|------|-----------|---------|-------|------------|
| 1134 | Tin | **Intake (cold) water temp** | ÷10 °C | confirmed |
| 1135 | Tout | **Outlet (heated) water temp** | ÷10 °C | confirmed |
| 1136 | — | Internal/ambient probe | ÷10 °C | likely |
| 1138 | Aktualna moc | **Power draw (live)** | W | confirmed |
| 1139 | Przepływ | **Flow rate** | ÷10 L/min | strong (energy balance) |
| 1140 | — | Display/working temp copy | ÷10 °C | partial |
| 1143 | — | Model/installed power | W | 24000 |
| 1144 | Moc podgrzewacza | Configured heater power | W | confirmed (18000) |
| 1146–1152 | — | RTC Y/M/D/wd/h/m/s | — | confirmed |
| 1276 | — | Serial suffix (ppe4_000XXXXX) | — | confirmed |
| 1388 | Maksymalna temperatura | Max temperature limit | ÷10 °C | confirmed |
| 1390 | — | **Selected profile index** (0..2) | — | confirmed |
| 1391 | Ustawienie temperatury | **Active working setpoint** | ÷10 °C | confirmed (writable) |
| 1392 | Profil 1 | Profile 1 preset | ÷10 °C | confirmed |
| 1393 | Profil 2 | Profile 2 preset | ÷10 °C | confirmed |
| 1394 | Profil 3 | Profile 3 preset | ÷10 °C | confirmed |

Notes:

- The **active setpoint** that drives heating is `1391`. Selecting a profile
  copies that profile's preset (`1392 + index`) into `1391`; the main dial edits
  `1391` directly.
- **Daily/weekly/yearly energy (kWh) and water (l) totals** are shown on the
  app's *Statystyki zużycia* screen (with cost in zł), but are **not** in the
  polled register region — they appear to come from a separate history endpoint.
  This integration instead derives running totals by integrating `1138`/`1139`
  over time (Energy-dashboard compatible).
- Many other registers in 1000–1440 carry schedule/config data and are not yet
  decoded (see `raw-register-dump.txt`).

## Writing

**Confirmed** (captured from the official app via an HTTP proxy, and verified
with reversible no-op writes from this integration):

```
POST http://<host>/api/write
Content-Type: application/json

{"1393":450}                       # string keys, integer values (x10 for temps)

-> {"ver":"1.0","status":"OK","status_value":"0"}
```

Notes:

- Writes go to a dedicated `/api/write` endpoint — **not** `/api/<addr>`.
- The official app sends the whole profile block in one request, e.g.
  `{"1390":0,"1391":340,"1392":420,"1393":450,"1394":500}`, but the firmware
  accepts any subset, so a single-register map works fine.
- Success is `status:"OK"`; failures return `status:"ERROR"` with a negative
  `status_value` (observed: `-1` body present but unparseable for the old
  per-address guess, `-2` no body, `-11` bad address, `-14` bad count).
- Setpoint register is `1392 + active profile`; the active profile is `1390`.
