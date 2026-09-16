"""The Adaptive Growth Light custom integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, FRONTEND_DIR, FRONTEND_URL
from .coordinator import AdaptiveGrowthLightCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TIME,
]


try:
    from homeassistant.components.http import StaticPathConfig
except ImportError:
    StaticPathConfig = None


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration and register frontend Lovelace card static path."""
    card_path = Path(__file__).parent / FRONTEND_DIR / "adaptive-growth-light-card.js"
    if hasattr(hass, "http") and hass.http and card_path.exists():
        if hasattr(hass.http, "async_register_static_paths") and StaticPathConfig:
            await hass.http.async_register_static_paths([
                StaticPathConfig(
                    url_path=FRONTEND_URL,
                    path=str(card_path),
                    cache_headers=False,
                )
            ])
        elif hasattr(hass.http, "register_static_path"):
            hass.http.register_static_path(
                FRONTEND_URL,
                str(card_path),
                cache_headers=False,
            )
        _LOGGER.debug("Registered static path for Adaptive Growth Light Card: %s", FRONTEND_URL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Adaptive Growth Light from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = AdaptiveGrowthLightCoordinator(hass, entry.entry_id, entry.data)
    await coordinator.async_setup()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Adaptive Growth Light config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: AdaptiveGrowthLightCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.async_unload()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
