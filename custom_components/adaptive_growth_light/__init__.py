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


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend static path and automatically register the Lovelace card."""
    if hass.data.setdefault(f"{DOMAIN}_frontend_registered", False):
        return
    hass.data[f"{DOMAIN}_frontend_registered"] = True

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

    # Automatically load the card module in Home Assistant frontend
    if "frontend" in hass.config.components:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, FRONTEND_URL)
        _LOGGER.debug("Auto-registered Lovelace card module URL: %s", FRONTEND_URL)

    # Also automatically register in Lovelace storage resources if available
    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data and hasattr(lovelace_data, "resources"):
            res_col = lovelace_data.resources
            if hasattr(res_col, "async_items") and hasattr(res_col, "async_create_item"):
                if not getattr(res_col, "loaded", True):
                    await res_col.async_load()
                existing_urls = [item.get("url") for item in res_col.async_items()]
                if FRONTEND_URL not in existing_urls:
                    await res_col.async_create_item({
                        "res_type": "module",
                        "url": FRONTEND_URL,
                    })
                    _LOGGER.info("Auto-registered %s in Lovelace dashboard resources", FRONTEND_URL)
    except Exception as err:
        _LOGGER.debug("Could not auto-add to Lovelace storage collection: %s", err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration and register frontend Lovelace card."""
    await async_register_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Adaptive Growth Light from a config entry."""
    await async_register_frontend(hass)
    hass.data.setdefault(DOMAIN, {})

    sw_version = "1.1.6"
    try:
        from homeassistant.loader import async_get_integration
        integration = await async_get_integration(hass, DOMAIN)
        if integration and integration.version:
            sw_version = str(integration.version)
    except Exception:
        pass

    coordinator = AdaptiveGrowthLightCoordinator(
        hass, entry.entry_id, entry.data, sw_version=sw_version
    )
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
