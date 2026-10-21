"""Shared entity base for Kospel PPE4."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import KospelPPE4Coordinator


class KospelPPE4Entity(CoordinatorEntity[KospelPPE4Coordinator]):
    """Base entity tying everything to one PPE4 device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KospelPPE4Coordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.serial)},
            name=DEFAULT_NAME,
            manufacturer="Kospel",
            model="PPE4",
            serial_number=coordinator.serial,
            configuration_url=f"http://{coordinator.client.host}/",
        )
