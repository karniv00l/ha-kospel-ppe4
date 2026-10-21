"""Profile selector for Kospel PPE4."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import KospelPPE4ConfigEntry
from .const import PROFILE_COUNT, REG_ACTIVE_PROFILE
from .coordinator import KospelPPE4Coordinator
from .entity import KospelPPE4Entity

PROFILE_OPTIONS = [f"Profile {i + 1}" for i in range(PROFILE_COUNT)]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KospelPPE4ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([KospelPPE4ProfileSelect(entry.runtime_data)])


class KospelPPE4ProfileSelect(KospelPPE4Entity, SelectEntity):
    """Selects the active temperature profile (1..3)."""

    _attr_translation_key = "profile"
    _attr_icon = "mdi:format-list-numbered"
    _attr_options = PROFILE_OPTIONS

    def __init__(self, coordinator: KospelPPE4Coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}_profile"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get(REG_ACTIVE_PROFILE)
        if idx is None or not 0 <= idx < PROFILE_COUNT:
            return None
        return PROFILE_OPTIONS[idx]

    async def async_select_option(self, option: str) -> None:
        idx = PROFILE_OPTIONS.index(option)
        await self.coordinator.async_select_profile(idx)
