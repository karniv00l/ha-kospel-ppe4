"""Sensors for Kospel PPE4."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import KospelPPE4ConfigEntry
from .const import (
    DECI,
    MARKER_UNUSED,
    REG_ENERGY_TODAY,
    REG_FLOW,
    REG_HEATER_POWER,
    REG_POWER,
    REG_POWER_INSTALLED,
    REG_TEMP_INTAKE,
    REG_TEMP_INTERNAL,
    REG_TEMP_OUTLET,
    REG_WATER_TODAY,
)
from .coordinator import KospelPPE4Coordinator
from .entity import KospelPPE4Entity


@dataclass(frozen=True, kw_only=True)
class KospelSensorDescription(SensorEntityDescription):
    """Describes a PPE4 sensor sourced from one register (or a 32-bit pair)."""

    register: int
    # For 32-bit values: the register holding the high word.
    register_hi: int | None = None
    convert: Callable[[int], float] = float


def _deci(v: int) -> float:
    return v / DECI


def _wh_to_kwh(v: int) -> float:
    return v / 1000.0


SENSORS: tuple[KospelSensorDescription, ...] = (
    KospelSensorDescription(
        key="intake_temp",
        translation_key="intake_temp",
        register=REG_TEMP_INTAKE,
        convert=_deci,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    KospelSensorDescription(
        key="outlet_temp",
        translation_key="outlet_temp",
        register=REG_TEMP_OUTLET,
        convert=_deci,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    KospelSensorDescription(
        key="power",
        translation_key="power",
        register=REG_POWER,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    KospelSensorDescription(
        key="flow_rate",
        translation_key="flow_rate",
        register=REG_FLOW,
        convert=_deci,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    # The heater's own daily counters (what the app's statistics show). They
    # reset at the heater's midnight; TOTAL_INCREASING treats that as a new
    # meter cycle, so the Energy dashboard and utility meters keep summing.
    KospelSensorDescription(
        key="energy",
        translation_key="energy",
        register=REG_ENERGY_TODAY,
        register_hi=REG_ENERGY_TODAY + 1,
        convert=_wh_to_kwh,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    KospelSensorDescription(
        key="water",
        translation_key="water",
        register=REG_WATER_TODAY,
        register_hi=REG_WATER_TODAY + 1,
        convert=_deci,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
    ),
    KospelSensorDescription(
        key="internal_temp",
        translation_key="internal_temp",
        register=REG_TEMP_INTERNAL,
        convert=_deci,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    KospelSensorDescription(
        key="power_installed",
        translation_key="power_installed",
        register=REG_POWER_INSTALLED,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KospelSensorDescription(
        key="heater_power",
        translation_key="heater_power",
        register=REG_HEATER_POWER,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KospelPPE4ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        KospelPPE4Sensor(coordinator, description) for description in SENSORS
    )


class KospelPPE4Sensor(KospelPPE4Entity, SensorEntity):
    """A single register surfaced as a sensor."""

    entity_description: KospelSensorDescription

    def __init__(
        self,
        coordinator: KospelPPE4Coordinator,
        description: KospelSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.serial}_{description.key}"

    @property
    def native_value(self) -> float | None:
        description = self.entity_description
        raw = self.coordinator.data.get(description.register)
        if raw is None or raw in MARKER_UNUSED:
            return None
        if description.register_hi is not None:
            hi = self.coordinator.data.get(description.register_hi)
            if hi is None:
                return None
            raw |= hi << 16
        return description.convert(raw)
