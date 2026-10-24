"""Editable profile presets for Kospel PPE4."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import KospelPPE4ConfigEntry
from .const import (
    DECI,
    MAX_TEMP,
    MIN_TEMP,
    PROFILE_COUNT,
    REG_MAX_TEMP,
    TEMP_STEP,
)
from .coordinator import KospelPPE4Coordinator
from .entity import KospelPPE4Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KospelPPE4ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        KospelPPE4ProfileNumber(coordinator, i) for i in range(1, PROFILE_COUNT + 1)
    )


class KospelPPE4ProfileNumber(KospelPPE4Entity, NumberEntity):
    """One editable Profil preset temperature."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = MIN_TEMP
    _attr_native_step = TEMP_STEP
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: KospelPPE4Coordinator, profile: int) -> None:
        super().__init__(coordinator)
        self._register = coordinator.profile_setpoint_register(profile)
        self._attr_translation_key = f"profile_{profile}"
        self._attr_unique_id = f"{coordinator.serial}_profile_{profile}"

    @property
    def native_max_value(self) -> float:
        raw = self.coordinator.data.get(REG_MAX_TEMP)
        return raw / DECI if raw else MAX_TEMP

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get(self._register)
        return None if raw is None else raw / DECI

    async def async_set_native_value(self, value: float) -> None:
        # If this profile is selected, the heater picks up the new preset itself.
        await self.coordinator.async_write_and_refresh(
            {self._register: int(round(value * DECI))}
        )
