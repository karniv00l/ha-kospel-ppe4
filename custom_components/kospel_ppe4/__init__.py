"""The Kospel PPE4 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KospelPPE4Client
from .const import CONF_HOST
from .coordinator import KospelPPE4Coordinator

type KospelPPE4ConfigEntry = ConfigEntry[KospelPPE4Coordinator]

PLATFORMS: list[Platform] = [
    Platform.WATER_HEATER,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: KospelPPE4ConfigEntry
) -> bool:
    """Set up Kospel PPE4 from a config entry."""
    session = async_get_clientsession(hass)
    client = KospelPPE4Client(entry.data[CONF_HOST], session)
    coordinator = KospelPPE4Coordinator(hass, entry, client)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: KospelPPE4ConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
