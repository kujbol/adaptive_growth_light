"""Unit tests for coordinator runtime logic."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import zoneinfo
import pytest

from custom_components.adaptive_growth_light.coordinator import AdaptiveGrowthLightCoordinator
from custom_components.adaptive_growth_light.const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
)

TZ_WARSAW = zoneinfo.ZoneInfo("Europe/Warsaw")


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.config.latitude = 52.2297
    hass.config.longitude = 21.0122
    hass.config.elevation = 100.0
    hass.services.async_call = AsyncMock()
    hass.states.get = MagicMock(return_value=MagicMock(state="off"))
    return hass


@pytest.mark.asyncio
async def test_coordinator_initialization_and_recalculate(mock_hass):
    data = {
        CONF_NAME: "Bathroom Plants",
        CONF_TARGET_ENTITY: "switch.bathroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    coordinator = AdaptiveGrowthLightCoordinator(mock_hass, "test_entry_1", data)

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


@pytest.mark.asyncio
async def test_coordinator_dynamic_setters(mock_hass):
    data = {
        CONF_NAME: "Bathroom Plants",
        CONF_TARGET_ENTITY: "switch.bathroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    coordinator = AdaptiveGrowthLightCoordinator(mock_hass, "test_entry_1", data)

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


@pytest.mark.asyncio
async def test_seasonal_matrix_from_coordinator(mock_hass):
    data = {
        CONF_NAME: "Living Room Monstera",
        CONF_TARGET_ENTITY: "light.monstera_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    coordinator = AdaptiveGrowthLightCoordinator(mock_hass, "test_entry_2", data)
    matrix = coordinator.get_seasonal_matrix()
    assert len(matrix) == 12
    for m in matrix:
        assert "month" in m
        assert "natural_hours" in m
        assert "supplementary_hours" in m
