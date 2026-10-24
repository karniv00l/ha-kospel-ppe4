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

- The **actual heating target is `1391`** (the working setpoint / main dial).
  Proven empirically: with Profile 1 *highlighted* (`1390`=0, preset `1392`=42 °C)
  but `1391`=45 °C, running water heated the outlet to **45 °C**, not 42 °C.
- Register `1390` only marks which profile is *highlighted* in the app — it does
  **not** change the target, and the app does not copy a preset into `1391` when
  you select a profile. This integration therefore treats the "active profile" as
  the one whose preset equals `1391`, and when you select a profile it copies that
  preset into `1391` so the choice actually takes effect.
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
- The body must be **compact JSON with no whitespace**. `{"1391": 450}` (note
  the space) is rejected with `status_value` `-10`, "A character that is not
  allowed was used."; `{"1391":450}` is accepted.
- The official app sends the whole profile block in one request, e.g.
  `{"1390":0,"1391":340,"1392":420,"1393":450,"1394":500}`, but the firmware
  accepts any subset, so a single-register map works fine.
- Success is `status:"OK"`; failures return `status:"ERROR"` with a negative
  `status_value` (observed: `-1` body present but unparseable for the old
  per-address guess, `-2` no body, `-10` disallowed character / path of 10+
  characters, `-11` bad address, `-14` bad count).
- The heating target is `1391`; `1390` only highlights a profile (see the
  register notes above).
