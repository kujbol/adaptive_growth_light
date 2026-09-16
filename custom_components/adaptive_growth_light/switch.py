"""Master automation switch for Adaptive Growth Light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
        """Extra state attributes."""
        return {
            "target_entity": self.coordinator.target_entity,
            "lighting_mode": self.coordinator.lighting_mode,
            "target_photoperiod": self.coordinator.target_photoperiod,
            "daylight_overlap": self.coordinator.daylight_overlap,
        }
