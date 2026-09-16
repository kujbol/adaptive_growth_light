"""Sensors for Adaptive Growth Light integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AdaptiveGrowthLightCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all sensor entities for this config entry."""
    coordinator: AdaptiveGrowthLightCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        AdaptiveGrowthLightStatusSensor(coordinator, entry),
        AdaptiveGrowthLightNextSessionSensor(coordinator, entry),
        AdaptiveGrowthLightSupplementaryHoursSensor(coordinator, entry),
        AdaptiveGrowthLightNaturalDaylightSensor(coordinator, entry),
        AdaptiveGrowthLightSeasonalProfileSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class AdaptiveGrowthLightBaseSensor(SensorEntity):
    """Base sensor for Adaptive Growth Light."""

    _attr_has_entity_name = True

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


class AdaptiveGrowthLightStatusSensor(AdaptiveGrowthLightBaseSensor):
    """Sensor reporting current plant lighting status."""

    _attr_icon = "mdi:sprout"

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Status"
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str:
        """Return current status string."""
        return self.coordinator.status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Additional state details."""
        plan = self.coordinator.today_plan
        return {
            "target_entity": self.coordinator.target_entity,
            "is_enabled": self.coordinator.is_enabled,
            "sunrise": plan.sunrise.isoformat() if plan and plan.sunrise else None,
            "sunset": plan.sunset.isoformat() if plan and plan.sunset else None,
        }


class AdaptiveGrowthLightNextSessionSensor(AdaptiveGrowthLightBaseSensor):
    """Sensor displaying upcoming session information."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Next Session"
        self._attr_unique_id = f"{entry.entry_id}_next_session"

    @property
    def native_value(self) -> str | None:
        """Return formatted description of next session."""
        next_s = self.coordinator.next_session
        if not next_s or not next_s.start:
            return "None scheduled"

        if not self.coordinator.is_enabled:
            return "Automation paused"

        # e.g. "Morning: 05:30 (2.5h)"
        start_str = next_s.start.strftime("%H:%M")
        dur_h = round(next_s.duration.total_seconds() / 3600.0, 1)
        type_str = next_s.session_type.capitalize()
        return f"{type_str} at {start_str} ({dur_h}h)"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return raw session details."""
        next_s = self.coordinator.next_session
        if not next_s or not next_s.start:
            return {}

        return {
            "session_type": next_s.session_type,
            "start_time": next_s.start.isoformat(),
            "end_time": next_s.end.isoformat() if next_s.end else None,
            "duration_hours": round(next_s.duration.total_seconds() / 3600.0, 2),
            "seconds_until": round(next_s.seconds_until),
        }


class AdaptiveGrowthLightSupplementaryHoursSensor(AdaptiveGrowthLightBaseSensor):
    """Sensor reporting calculated supplementary light needed today."""

    _attr_icon = "mdi:weather-sunny-alert"
    _attr_native_unit_of_measurement = "h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Supplementary Hours Today"
        self._attr_unique_id = f"{entry.entry_id}_supplementary_hours"

    @property
    def native_value(self) -> float:
        """Return hours of supplementary lighting."""
        if self.coordinator.today_plan:
            return self.coordinator.today_plan.supplementary_hours
        return 0.0


class AdaptiveGrowthLightNaturalDaylightSensor(AdaptiveGrowthLightBaseSensor):
    """Sensor reporting natural daylight duration today."""

    _attr_icon = "mdi:weather-sunny"
    _attr_native_unit_of_measurement = "h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Natural Daylight Today"
        self._attr_unique_id = f"{entry.entry_id}_natural_daylight"

    @property
    def native_value(self) -> float:
        """Return hours of natural daylight."""
        if self.coordinator.today_plan:
            return self.coordinator.today_plan.natural_daylight_hours
        return 0.0


class AdaptiveGrowthLightSeasonalProfileSensor(AdaptiveGrowthLightBaseSensor):
    """Sensor carrying the 12-month solar and photoperiod breakdown."""

    _attr_icon = "mdi:chart-bell-curve-cumulative"

    def __init__(self, coordinator: AdaptiveGrowthLightCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_name = "Seasonal Profile"
        self._attr_unique_id = f"{entry.entry_id}_seasonal_profile"

    @property
    def native_value(self) -> str:
        """Return summary state."""
        return f"{self.coordinator.target_photoperiod}h target"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return 12 months array for the frontend card."""
        return {
            "months": self.coordinator.get_seasonal_matrix(),
            "target_photoperiod": self.coordinator.target_photoperiod,
            "lighting_mode": self.coordinator.lighting_mode,
            "morning_split": self.coordinator.morning_split,
            "daylight_overlap": self.coordinator.daylight_overlap,
        }
