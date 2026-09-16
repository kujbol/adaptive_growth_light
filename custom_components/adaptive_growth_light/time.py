"""Time entities for Adaptive Growth Light cut-off controls."""

from __future__ import annotations

from datetime import time
import logging

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AdaptiveGrowthLightCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up time entities for this config entry."""
    coordinator: AdaptiveGrowthLightCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        AdaptiveGrowthLightEarliestStartTime(coordinator, entry),
        AdaptiveGrowthLightLatestEndTime(coordinator, entry),
    ])


class AdaptiveGrowthLightBaseTime(TimeEntity):
    """Base time entity for Adaptive Growth Light cut-off controls."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AdaptiveGrowthLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.coordinator.name,
            manufacturer="Adaptive Growth Light",
            model="Photoperiod Controller",
            sw_version=self.coordinator.sw_version,
        )

    async def async_added_to_hass(self) -> None:
        """Register coordinator update listener."""
        self.async_on_remove(self.coordinator.add_listener(self.async_write_ha_state))


class AdaptiveGrowthLightEarliestStartTime(AdaptiveGrowthLightBaseTime):
    """Control for earliest morning grow light turn-on cut-off."""

    _attr_icon = "mdi:alarm"

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Earliest Morning Start"
        self._attr_unique_id = f"{entry.entry_id}_earliest_start"

    @property
    def native_value(self) -> time | None:
        """Return current earliest turn-on time."""
        return self.coordinator.earliest_start

    async def async_set_value(self, value: time) -> None:
        """Set new earliest turn-on time."""
        await self.coordinator.async_set_earliest_start(value)


class AdaptiveGrowthLightLatestEndTime(AdaptiveGrowthLightBaseTime):
    """Control for latest evening grow light turn-off cut-off."""

    _attr_icon = "mdi:bed-clock"

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Latest Evening End"
        self._attr_unique_id = f"{entry.entry_id}_latest_end"

    @property
    def native_value(self) -> time | None:
        """Return current latest turn-off time."""
        return self.coordinator.latest_end

    async def async_set_value(self, value: time) -> None:
        """Set new latest turn-off time."""
        await self.coordinator.async_set_latest_end(value)
