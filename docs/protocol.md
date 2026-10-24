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
| 1139 | Przepływ | **Flow rate** | ÷10 L/min | confirmed (reads ~12–25% high vs. counters) |
| 1140 | — | **Effective target** (what the heater aims for) | ÷10 °C | confirmed (read-only) |
| 1143 | — | Model/installed power | W | 24000 |
| 1144 | Moc podgrzewacza | Configured heater power | W | confirmed (18000) |
| 1146–1152 | — | RTC Y/M/D/wd/h/m/s | — | confirmed |
| 1276 | — | Serial suffix (ppe4_000XXXXX) | — | confirmed |
| 1388 | Maksymalna temperatura | Max temperature limit | ÷10 °C | confirmed |
| 1390 | — | **Mode**: 0 = manual, 1..3 = Profil 1..3 | — | confirmed (writable) |
| 1391 | Ustawienie temperatury | **Manual setpoint** | ÷10 °C | confirmed (writable) |
| 1392 | Profil 1 | Profile 1 preset | ÷10 °C | confirmed |
| 1393 | Profil 2 | Profile 2 preset | ÷10 °C | confirmed |
| 1394 | Profil 3 | Profile 3 preset | ÷10 °C | confirmed |

Notes:

- **`1390` picks the target**: `0` = manual (heat to `1391`), `1`..`3` = heat to
  that profile's preset (`1392`..`1394`). The heater reports the result in
  **`1140`**. Observed:

  | `1390` | `1391` | `1392` (Profil 1) | `1140` |
  |--------|--------|-------------------|--------|
  | 0 | 340 | 420 | 340 (= `1391`) |
  | 0 | 450 | 420 | 450 (= `1391`; outlet reached 45 °C under flow) |
  | 1 | 450 | 400 | 400 (= Profil 1) |

- Selecting a profile in the app (captured) writes the profile number to `1390`
  and leaves `1391` unchanged. Profile numbers are **1-based**: going
  Profil 1 → Profil 3 → Profil 1 wrote `1390` = 3, then 1.
- An earlier version of these notes said `1390` only highlights a profile and
  `1391` is always the target. That was wrong: the heater was in manual mode
  (`1390` = 0) during that test.
- Many other registers in 1000–1440 carry schedule/config data and are not yet
  decoded (see `raw-register-dump.txt`).
- The flow register `1139` reads about 12–25% high compared with the heater's
  own water counters, so don't integrate it for volume. Use the counters
  below.

### Usage counters

The app's *Statystyki zużycia* screen reads these blocks (captured with a
proxy). Each block must be read **starting exactly at its first address**: a
read that starts elsewhere comes back empty (`"res":}`), even if it overlaps.

| Block | Read | Contents |
|-------|------|----------|
| Energy, daily | `GET /api/1448/30` | `1448`, `1449`: header (weekday, month); then 14 x 32-bit Wh |
| Energy, monthly | `GET /api/1520/48` | 24 x 32-bit Wh, two registers per month from January |
| Water, daily | `GET /api/1576/30` | `1576`, `1577`: header; then 14 x 32-bit values, x10 L |
| Water, monthly | `GET /api/1648/48` | 24 x 32-bit values, x10 L, two registers per month from January |

- 32-bit values are stored low word first: `value = lo | hi << 16`.
- Daily slots run newest first: `1450`/`1451` = today, `1452`/`1453` = yesterday,
  and so on. The app shows 7 days plus the previous week ("Poprzednio").
- Verified on 2026-10-24: water `1578..1584` = 53, 857, 739, 717
  (5.3 / 85.7 / 73.9 / 71.7 L, matching the app's Sat/Fri/Thu/Wed bars). October
  totals `1538` = 9118 Wh and `1666` = 2366 (236.6 L) equal the sums of the
  daily slots.
- Month slots: October = `1520 + 2*9` = `1538`. Which year the second half of
  each 48-register block holds hasn't been confirmed.

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
- To change the target, write `1390` (profile) or `{"1390":0,"1391":<t>}`
  (manual). Writing `1391` alone has no effect while a profile is selected.
