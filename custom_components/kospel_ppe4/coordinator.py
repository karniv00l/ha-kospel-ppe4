"""Data update coordinator for Kospel PPE4."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KospelPPE4Client, KospelPPE4Error
from .const import (
    DAY_BLOCK_COUNT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENERGY_DAY_BLOCK_START,
    LIVE_BLOCK_COUNT,
    LIVE_BLOCK_START,
    PROFILE_COUNT,
    PROFILE_MANUAL,
    REG_ACTIVE_PROFILE,
    REG_PROFILE_BASE,
    REG_SERIAL_SUFFIX,
    REG_SETPOINT,
    SETTINGS_BLOCK_COUNT,
    SETTINGS_BLOCK_START,
    WATER_DAY_BLOCK_START,
)

_LOGGER = logging.getLogger(__name__)


class KospelPPE4Coordinator(DataUpdateCoordinator[dict[int, int]]):
    """Polls the heater and holds the latest register snapshot."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: KospelPPE4Client,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )
        self.client = client
        self._serial: str | None = None

    async def _async_setup(self) -> None:
        """Read one-shot identity data at startup."""
        try:
            regs = await self.client.read_registers(REG_SERIAL_SUFFIX, 1)
        except KospelPPE4Error as err:
            raise UpdateFailed(f"Error reading identity: {err}") from err
        suffix = regs.get(REG_SERIAL_SUFFIX)
        if suffix is not None:
            self._serial = f"ppe4_{suffix:08d}"

    async def _async_update_data(self) -> dict[int, int]:
        try:
            data: dict[int, int] = {}
            data.update(
                await self.client.read_registers(LIVE_BLOCK_START, LIVE_BLOCK_COUNT)
            )
            data.update(
                await self.client.read_registers(
                    SETTINGS_BLOCK_START, SETTINGS_BLOCK_COUNT
                )
            )
            for start in (ENERGY_DAY_BLOCK_START, WATER_DAY_BLOCK_START):
                data.update(await self.client.read_registers(start, DAY_BLOCK_COUNT))
        except KospelPPE4Error as err:
            raise UpdateFailed(f"Error communicating with heater: {err}") from err
        return data

    # --- Convenience accessors --------------------------------------------

    @property
    def serial(self) -> str:
        return self._serial or f"ppe4_{self.client.host}"

    @property
    def active_profile(self) -> int | None:
        """Selected profile 1..PROFILE_COUNT, PROFILE_MANUAL (0), or None."""
        profile = self.data.get(REG_ACTIVE_PROFILE) if self.data else None
        if profile is None or not 0 <= profile <= PROFILE_COUNT:
            return None
        return profile

    def profile_setpoint_register(self, profile: int) -> int:
        """Return the register that holds a given (1-based) profile's preset."""
        return REG_PROFILE_BASE + profile - 1

    async def async_write_and_refresh(self, values: dict[int, int]) -> None:
        """Write one or more registers and refresh so the UI reflects it."""
        await self.client.write_registers(values)
        # Optimistically store the new values, then confirm on next poll.
        if self.data is not None:
            self.data.update(values)
            self.async_set_updated_data(self.data)
        await self.async_request_refresh()

    async def async_select_profile(self, profile: int) -> None:
        """Select a profile (1..3), or PROFILE_MANUAL to use the manual setpoint."""
        await self.async_write_and_refresh({REG_ACTIVE_PROFILE: profile})

    async def async_set_manual_target(self, value: int) -> None:
        """Switch to manual mode and aim for `value` (deci-degrees).

        Writing only the setpoint would have no effect while a profile is
        selected, and editing the active profile's preset would silently change
        a saved profile.
        """
        await self.async_write_and_refresh(
            {REG_ACTIVE_PROFILE: PROFILE_MANUAL, REG_SETPOINT: value}
        )
