"""Water heater entity for Kospel PPE4 (instantaneous water heater)."""

from __future__ import annotations

from homeassistant.components.water_heater import (
    STATE_ELECTRIC,
    STATE_OFF,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import KospelPPE4ConfigEntry
from .const import (
    DECI,
    MAX_TEMP,
    MIN_TEMP,
    REG_MAX_TEMP,
    REG_POWER,
    REG_TEMP_OUTLET,
    TEMP_STEP,
)
from .coordinator import KospelPPE4Coordinator
from .entity import KospelPPE4Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KospelPPE4ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([KospelPPE4WaterHeater(entry.runtime_data)])


class KospelPPE4WaterHeater(KospelPPE4Entity, WaterHeaterEntity):
    """The heater's outlet-water temperature control."""

    _attr_name = None  # use the device name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_target_temperature_step = TEMP_STEP
    _attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE

    def __init__(self, coordinator: KospelPPE4Coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}_water_heater"

    @property
    def max_temp(self) -> float:
        raw = self.coordinator.data.get(REG_MAX_TEMP)
        return raw / DECI if raw else MAX_TEMP

    @property
    def current_operation(self) -> str:
        """Electric while actively heating (drawing power), otherwise off."""
        return STATE_ELECTRIC if self.coordinator.data.get(REG_POWER) else STATE_OFF

    @property
    def current_temperature(self) -> float | None:
        raw = self.coordinator.data.get(REG_TEMP_OUTLET)
        return None if raw is None else raw / DECI

    @property
    def target_temperature(self) -> float | None:
        raw = self.coordinator.data.get(self.coordinator.target_temp_register)
        return None if raw is None else raw / DECI

    async def async_set_temperature(self, **kwargs: float) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        value = int(round(temperature * DECI))
        await self.coordinator.async_write_and_refresh(
            {self.coordinator.target_temp_register: value}
        )
