"""End-to-end integration test for Adaptive Growth Light setup and entity registration."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_growth_light.const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
    DOMAIN,
)


async def test_full_integration_setup_and_unload(hass: HomeAssistant) -> None:
    """Test setting up the entry, entities registration, and unload."""
    await hass.config.async_set_time_zone("Europe/Warsaw")
    await hass.config.async_update(latitude=52.2297, longitude=21.0122, elevation=100)

    # Pre-create target light state
    hass.states.async_set("switch.bathroom_grow_light", "off")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bathroom Grow Light",
        data={
            CONF_NAME: "Bathroom Grow Light",
            CONF_TARGET_ENTITY: "switch.bathroom_grow_light",
            CONF_TARGET_PHOTOPERIOD: 14.0,
            CONF_LIGHTING_MODE: "both",
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Verify coordinator stored
    assert entry.entry_id in hass.data[DOMAIN]

    # Verify switch entity exists
    switch_state = hass.states.get("switch.bathroom_grow_light_automation")
    assert switch_state is not None
    assert switch_state.state == "on"

    # Verify sensor entities exist
    status_state = hass.states.get("sensor.bathroom_grow_light_status")
    assert status_state is not None
    assert status_state.state in [
        "supplementing_morning",
        "supplementing_evening",
        "daylight_active",
        "night_idle",
    ]

    target_number = hass.states.get("number.bathroom_grow_light_target_photoperiod")
    assert target_number is not None
    assert float(target_number.state) == 14.0

    # Unload entry
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.entry_id not in hass.data[DOMAIN]


async def test_async_setup_with_http(hass: HomeAssistant) -> None:
    """Verify async_setup registers static path with modern async_register_static_paths."""
    from unittest.mock import AsyncMock, MagicMock
    from custom_components.adaptive_growth_light import async_setup

    mock_http = MagicMock()
    mock_http.async_register_static_paths = AsyncMock()
    hass.http = mock_http

    assert await async_setup(hass, {}) is True
    mock_http.async_register_static_paths.assert_awaited_once()

