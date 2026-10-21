"""Constants for the Kospel PPE4 integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "kospel_ppe4"

DEFAULT_NAME: Final = "Kospel PPE4"
DEFAULT_SCAN_INTERVAL: Final = 15  # seconds
DEFAULT_TIMEOUT: Final = 6  # seconds

CONF_HOST: Final = "host"

# --- MODBUS-over-HTTP registers (16-bit, little gaps between blocks) ---------
#
# The PPE4 Wi-Fi module serves a MODBUS-over-HTTP API with no authentication:
#
#   GET http://<host>/api/<start>/<count>
#     -> {"ver":"1.0","status":"OK","status_value":"0",
#         "res":{"<addr>":<value>, ...}}
#
# Values are unsigned 16-bit integers. Temperatures are deci-degrees (x10),
# e.g. 420 == 42.0 degC. A few sensor slots use 0xFFFF (65535) / 0xAAAA (43690)
# as "unused" / "not present" markers.
#
# The map below was reverse-engineered from a live PPE4 (serial ppe4_000XXXXX).
# Addresses are confirmed where noted; others are best-effort and exposed as
# diagnostic sensors so they can be identified over time.

# Live / measured values ------------------------------------------------------
# Confirmed by watching the registers while hot water actually flowed:
REG_TEMP_INTAKE: Final = 1134  # confirmed: intake (cold) water temp, x10 degC
REG_TEMP_OUTLET: Final = 1135  # confirmed: outlet (heated) water temp, x10 degC
REG_TEMP_INTERNAL: Final = 1136  # internal/ambient probe, x10 degC (~22, stable)
REG_POWER: Final = 1138  # confirmed: instantaneous power draw ("Aktualna moc"), W
REG_FLOW: Final = 1139  # flow rate ("Przepływ"), x10 L/min (0 when idle)

# Installed-power configuration (not live draw) --------------------------------
REG_POWER_INSTALLED: Final = 1143  # watts, model/nameplate power (e.g. 24000)
REG_HEATER_POWER: Final = 1144  # watts, configured heater power "Moc podgrzewacza" (18000)

# Real-time clock (confirmed) -------------------------------------------------
REG_RTC_YEAR: Final = 1146  # 2000 + value
REG_RTC_MONTH: Final = 1147
REG_RTC_DAY: Final = 1148
REG_RTC_WEEKDAY: Final = 1149
REG_RTC_HOUR: Final = 1150
REG_RTC_MINUTE: Final = 1151
REG_RTC_SECOND: Final = 1152

# Settings / setpoints --------------------------------------------------------
REG_MAX_TEMP: Final = 1388  # confirmed: max temperature limit "Maksymalna temp." (x10)
REG_ACTIVE_PROFILE: Final = 1390  # confirmed: selected profile index (0..2)
REG_SETPOINT: Final = 1391  # confirmed: active working setpoint "Ustawienie temp." (x10)
REG_PROFILE_BASE: Final = 1392  # Profil 1/2/3 presets at BASE+0/1/2 (x10 degC)
PROFILE_COUNT: Final = 3

# Identity --------------------------------------------------------------------
REG_SERIAL_SUFFIX: Final = 1276  # confirmed: numeric suffix of ppe4_000XXXXX

# Setpoint limits (degC). PPE4 instantaneous heaters top out around 60 degC.
MIN_TEMP: Final = 20.0
MAX_TEMP: Final = 60.0
TEMP_STEP: Final = 1.0

# Scaling helpers
DECI: Final = 10.0

# The contiguous block we poll each cycle (covers live values + RTC).
LIVE_BLOCK_START: Final = 1130
LIVE_BLOCK_COUNT: Final = 30  # 1130..1159
# Settings block (profiles).
SETTINGS_BLOCK_START: Final = 1388
SETTINGS_BLOCK_COUNT: Final = 8  # 1388..1395

# 0xFFFF / 0xAAAA markers that mean "no sensor / unused".
MARKER_UNUSED: Final = frozenset({0xFFFF, 0xAAAA})
