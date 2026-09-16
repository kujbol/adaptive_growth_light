"""Master automation switch for Adaptive Growth Light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AdaptiveGrowthLightCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Adaptive Growth Light switch entity."""
    coordinator: AdaptiveGrowthLightCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdaptiveGrowthLightMasterSwitch(coordinator, entry)])


class AdaptiveGrowthLightMasterSwitch(SwitchEntity):
    """Switch to enable or disable the supplementary lighting automation."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:sun-clock"

    def __init__(
        self,
        coordinator: AdaptiveGrowthLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_name = "Automation"
        self._attr_unique_id = f"{entry.entry_id}_automation_switch"

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
        """Register callbacks when added to Home Assistant."""
        self.async_on_remove(self.coordinator.add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        """Return True if automation is enabled."""
        return self.coordinator.is_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable automation."""
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable automation."""
        await self.coordinator.async_set_enabled(False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra state attributes for instant card synchronization."""
        plan = self.coordinator.today_plan
        next_s = self.coordinator.next_session

        morn_start = plan.morning_session.start.strftime("%H:%M") if plan and plan.morning_session else None
        morn_end = plan.morning_session.end.strftime("%H:%M") if plan and plan.morning_session else None
        eve_start = plan.evening_session.start.strftime("%H:%M") if plan and plan.evening_session else None
        eve_end = plan.evening_session.end.strftime("%H:%M") if plan and plan.evening_session else None

        next_str = "None scheduled"
        if next_s and next_s.start:
            dur_h = round(next_s.duration.total_seconds() / 3600.0, 1)
            next_str = f"{next_s.session_type.capitalize()} at {next_s.start.strftime('%H:%M')} ({dur_h}h)"

        earliest_turn_on = "--:--"
        seasonal_months: list[dict[str, Any]] = []
        try:
            earliest_info = self.coordinator.get_annual_earliest_turn_on()
            if earliest_info:
                earliest_turn_on = earliest_info.get("effective_time", "--:--")
        except Exception:
            pass

        try:
            seasonal_months = self.coordinator.get_seasonal_matrix()
        except Exception:
            pass

        return {
            "target_entity": self.coordinator.target_entity,
            "lighting_mode": self.coordinator.lighting_mode,
            "target_photoperiod": self.coordinator.target_photoperiod,
            "morning_split": self.coordinator.morning_split,
            "daylight_overlap": self.coordinator.daylight_overlap,
            "status": self.coordinator.status,
            "is_enabled": self.coordinator.is_enabled,
            "sunrise": plan.sunrise.isoformat() if plan and plan.sunrise else None,
            "sunset": plan.sunset.isoformat() if plan and plan.sunset else None,
            "today_morning_start": morn_start,
            "today_morning_end": morn_end,
            "today_evening_start": eve_start,
            "today_evening_end": eve_end,
            "supplementary_hours": round(plan.supplementary_hours, 1) if plan else 0.0,
            "natural_daylight_hours": round(plan.natural_daylight_hours, 1) if plan else 0.0,
            "earliest_turn_on": earliest_turn_on,
            "next_session_str": next_str,
            "seasonal_months": seasonal_months,
        }
