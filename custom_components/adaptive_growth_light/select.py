"""Select entity for lighting mode in Adaptive Growth Light."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LIGHTING_MODES
from .coordinator import AdaptiveGrowthLightCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the lighting mode select entity."""
    coordinator: AdaptiveGrowthLightCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdaptiveGrowthLightModeSelect(coordinator, entry)])


class AdaptiveGrowthLightModeSelect(SelectEntity):
    """Select entity to change the supplementary lighting mode."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:theme-light-dark"
    _attr_options = LIGHTING_MODES

    def __init__(
        self,
        coordinator: AdaptiveGrowthLightCoordinator,
        entry: ConfigEntry,
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_name = "Lighting Mode"
        self._attr_unique_id = f"{entry.entry_id}_lighting_mode"

    async def async_added_to_hass(self) -> None:
        """Register coordinator update listener."""
        self.async_on_remove(self.coordinator.add_listener(self.async_write_ha_state))

    @property
    def current_option(self) -> str:
        """Return currently selected lighting mode."""
        return self.coordinator.lighting_mode

    async def async_select_option(self, option: str) -> None:
        """Change the lighting mode."""
        if option in LIGHTING_MODES:
            await self.coordinator.async_set_lighting_mode(option)
