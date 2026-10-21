"""Sensors for Kospel PPE4."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    RestoreSensor,
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import KospelPPE4ConfigEntry
from .const import (
    DECI,
    MARKER_UNUSED,
    REG_FLOW,
    REG_HEATER_POWER,
    REG_POWER,
    REG_POWER_INSTALLED,
    REG_TEMP_INTAKE,
    REG_TEMP_INTERNAL,
    REG_TEMP_OUTLET,
)
from .coordinator import KospelPPE4Coordinator
from .entity import KospelPPE4Entity


@dataclass(frozen=True, kw_only=True)
class KospelSensorDescription(SensorEntityDescription):
    """Describes a PPE4 sensor sourced from one register."""

    register: int
    convert: Callable[[int], float] = float


def _deci(v: int) -> float:
    return v / DECI


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
    entities: list[SensorEntity] = [
        KospelPPE4Sensor(coordinator, description) for description in SENSORS
    ]
    # Derived running totals, integrated from the live power / flow readings.
    entities.append(
        KospelPPE4IntegratingSensor(
            coordinator,
            key="energy",
            translation_key="energy",
            source_register=REG_POWER,
            source_scale=1.0,  # register is already watts
            per_second=lambda w: w / 3_600_000.0,  # W -> kWh/s
            device_class=SensorDeviceClass.ENERGY,
            unit=UnitOfEnergy.KILO_WATT_HOUR,
        )
    )
    entities.append(
        KospelPPE4IntegratingSensor(
            coordinator,
            key="water",
            translation_key="water",
            source_register=REG_FLOW,
            source_scale=DECI,  # register is L/min x10
            per_second=lambda lpm: lpm / 60.0,  # L/min -> L/s
            device_class=SensorDeviceClass.WATER,
            unit=UnitOfVolume.LITERS,
        )
    )
    async_add_entities(entities)


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
        raw = self.coordinator.data.get(self.entity_description.register)
        if raw is None or raw in MARKER_UNUSED:
            return None
        return self.entity_description.convert(raw)


class KospelPPE4IntegratingSensor(KospelPPE4Entity, RestoreSensor):
    """A total_increasing sensor integrated from a live rate register.

    Integrates the instantaneous power (for energy) or flow (for water volume)
    over time using the trapezoidal rule between coordinator updates, and
    restores its accumulated value across restarts.
    """

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: KospelPPE4Coordinator,
        *,
        key: str,
        translation_key: str,
        source_register: int,
        source_scale: float,
        per_second: Callable[[float], float],
        device_class: SensorDeviceClass,
        unit: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}_{key}"
        self._attr_translation_key = translation_key
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._source_register = source_register
        self._source_scale = source_scale
        self._per_second = per_second
        self._total: float = 0.0
        self._last_ts = None
        self._last_rate: float | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            if last.native_value is not None:
                self._total = float(last.native_value)
        self._last_ts = dt_util.utcnow()

    def _current_rate(self) -> float | None:
        raw = self.coordinator.data.get(self._source_register)
        if raw is None or raw in MARKER_UNUSED:
            return None
        return self._per_second(raw / self._source_scale)

    @callback
    def _handle_coordinator_update(self) -> None:
        now = dt_util.utcnow()
        rate = self._current_rate()
        if rate is not None and self._last_ts is not None:
            dt = (now - self._last_ts).total_seconds()
            if dt > 0:
                prev = self._last_rate if self._last_rate is not None else rate
                self._total += (rate + prev) / 2.0 * dt
        self._last_ts = now
        self._last_rate = rate
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> float:
        return round(self._total, 4)
