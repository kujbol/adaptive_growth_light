"""Unit tests for coordinator runtime logic with real Home Assistant fixture."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.adaptive_growth_light.const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
)
from custom_components.adaptive_growth_light.coordinator import (
    AdaptiveGrowthLightCoordinator,
)


async def test_coordinator_initialization_and_recalculate(hass: HomeAssistant) -> None:
    # Set Home Assistant coordinates (Warsaw)
    await hass.config.async_set_time_zone("Europe/Warsaw")
    await hass.config.async_update(latitude=52.2297, longitude=21.0122, elevation=100)

    data = {
        CONF_NAME: "Bathroom Plants",
        CONF_TARGET_ENTITY: "switch.bathroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    coordinator = AdaptiveGrowthLightCoordinator(hass, "test_entry_1", data)

    # Initial recalculate
    coordinator.recalculate()

    assert coordinator.name == "Bathroom Plants"
    assert coordinator.target_entity == "switch.bathroom_grow_light"
    assert coordinator.target_photoperiod == 14.0
    assert coordinator.lighting_mode == "both"
    assert coordinator.morning_split == 50.0
    assert coordinator.daylight_overlap == 1.0
    assert coordinator.is_enabled is True
    assert coordinator.today_plan is not None
    assert coordinator.next_session is not None
    assert coordinator.status in [
        "supplementing_morning",
        "supplementing_evening",
        "daylight_active",
        "night_idle",
    ]


async def test_coordinator_dynamic_setters(hass: HomeAssistant) -> None:
    await hass.config.async_set_time_zone("Europe/Warsaw")
    await hass.config.async_update(latitude=52.2297, longitude=21.0122, elevation=100)

    data = {
        CONF_NAME: "Bathroom Plants",
        CONF_TARGET_ENTITY: "switch.bathroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    coordinator = AdaptiveGrowthLightCoordinator(hass, "test_entry_1", data)

    listener_called = False

    def on_update():
        nonlocal listener_called
        listener_called = True

    coordinator.add_listener(on_update)

    # Change target photoperiod
    await coordinator.async_set_target_photoperiod(16.0)
    assert coordinator.target_photoperiod == 16.0
    assert listener_called is True

    # Change mode
    listener_called = False
    await coordinator.async_set_lighting_mode("morning")
    assert coordinator.lighting_mode == "morning"
    assert listener_called is True

    # Change split
    listener_called = False
    await coordinator.async_set_morning_split(60.0)
    assert coordinator.morning_split == 60.0
    assert listener_called is True

    # Change overlap
    listener_called = False
    await coordinator.async_set_daylight_overlap(1.5)
    assert coordinator.daylight_overlap == 1.5
    assert listener_called is True

    # Disable
    listener_called = False
    await coordinator.async_set_enabled(False)
    assert coordinator.is_enabled is False
    assert coordinator.status == "disabled"
    assert listener_called is True


async def test_seasonal_matrix_from_coordinator(hass: HomeAssistant) -> None:
    await hass.config.async_set_time_zone("Europe/Warsaw")
    await hass.config.async_update(latitude=52.2297, longitude=21.0122, elevation=100)

    data = {
        CONF_NAME: "Living Room Monstera",
        CONF_TARGET_ENTITY: "light.monstera_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    coordinator = AdaptiveGrowthLightCoordinator(hass, "test_entry_2", data)
    matrix = coordinator.get_seasonal_matrix()
    assert len(matrix) == 12
    for m in matrix:
        assert "month" in m
        assert "natural_hours" in m
        assert "supplementary_hours" in m


async def test_coordinator_cutoffs_and_annual_earliest(hass: HomeAssistant) -> None:
    from datetime import time

    await hass.config.async_set_time_zone("Europe/Warsaw")
    await hass.config.async_update(latitude=52.2297, longitude=21.0122, elevation=100)

    data = {
        CONF_NAME: "Living Room Ficus",
        CONF_TARGET_ENTITY: "light.ficus_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
        "earliest_start": "06:30:00",
        "latest_end": "22:00:00",
    }
    coordinator = AdaptiveGrowthLightCoordinator(hass, "test_entry_3", data)
    assert coordinator.earliest_start == time(6, 30)
    assert coordinator.latest_end == time(22, 0)

    stats = coordinator.get_annual_earliest_turn_on()
    assert "effective_time" in stats
    assert "unclamped_time" in stats
    assert "is_clamped" in stats

    # Change cutoffs dynamically
    await coordinator.async_set_earliest_start(time(7, 0))
    assert coordinator.earliest_start == time(7, 0)

    await coordinator.async_set_latest_end("21:30:00")
    assert coordinator.latest_end == time(21, 30)
