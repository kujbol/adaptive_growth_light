"""Number entities for Adaptive Growth Light integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MAX_OVERLAP,
    MAX_PHOTOPERIOD,
    MAX_SPLIT,
    MIN_OVERLAP,
    MIN_PHOTOPERIOD,
    MIN_SPLIT,
    STEP_OVERLAP,
    STEP_PHOTOPERIOD,
    STEP_SPLIT,
)
from .coordinator import AdaptiveGrowthLightCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities for this config entry."""
    coordinator: AdaptiveGrowthLightCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        AdaptiveGrowthLightTargetPhotoperiodNumber(coordinator, entry),
        AdaptiveGrowthLightMorningSplitNumber(coordinator, entry),
        AdaptiveGrowthLightDaylightOverlapNumber(coordinator, entry),
    ])


class AdaptiveGrowthLightBaseNumber(NumberEntity):
    """Base number entity for Adaptive Growth Light."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: AdaptiveGrowthLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry

    async def async_added_to_hass(self) -> None:
        """Register coordinator update listener."""
        self.async_on_remove(self.coordinator.add_listener(self.async_write_ha_state))


class AdaptiveGrowthLightTargetPhotoperiodNumber(AdaptiveGrowthLightBaseNumber):
    """Control for target photoperiod in hours."""

    _attr_icon = "mdi:weather-sunny"
    _attr_native_unit_of_measurement = "h"
    _attr_native_min_value = MIN_PHOTOPERIOD
    _attr_native_max_value = MAX_PHOTOPERIOD
    _attr_native_step = STEP_PHOTOPERIOD

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Target Photoperiod"
        self._attr_unique_id = f"{entry.entry_id}_target_photoperiod"

    @property
    def native_value(self) -> float:
        """Return current target photoperiod."""
        return self.coordinator.target_photoperiod

    async def async_set_native_value(self, value: float) -> None:
        """Set new target photoperiod."""
        await self.coordinator.async_set_target_photoperiod(float(value))


class AdaptiveGrowthLightMorningSplitNumber(AdaptiveGrowthLightBaseNumber):
    """Control for morning split percentage in 'Both' mode."""

    _attr_icon = "mdi:fraction-one-half"
    _attr_native_unit_of_measurement = "%"
    _attr_native_min_value = MIN_SPLIT
    _attr_native_max_value = MAX_SPLIT
    _attr_native_step = STEP_SPLIT

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Morning Split"
        self._attr_unique_id = f"{entry.entry_id}_morning_split"

    @property
    def native_value(self) -> float:
        """Return current morning split percentage."""
        return self.coordinator.morning_split

    async def async_set_native_value(self, value: float) -> None:
        """Set new morning split percentage."""
        await self.coordinator.async_set_morning_split(float(value))


class AdaptiveGrowthLightDaylightOverlapNumber(AdaptiveGrowthLightBaseNumber):
    """Control for daylight overlap buffer in hours."""

    _attr_icon = "mdi:arrow-expand-horizontal"
    _attr_native_unit_of_measurement = "h"
    _attr_native_min_value = MIN_OVERLAP
    _attr_native_max_value = MAX_OVERLAP
    _attr_native_step = STEP_OVERLAP

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Daylight Overlap"
        self._attr_unique_id = f"{entry.entry_id}_daylight_overlap"

    @property
    def native_value(self) -> float:
        """Return current daylight overlap."""
        return self.coordinator.daylight_overlap

    async def async_set_native_value(self, value: float) -> None:
        """Set new daylight overlap."""
        await self.coordinator.async_set_daylight_overlap(float(value))
