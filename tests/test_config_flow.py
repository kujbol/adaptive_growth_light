"""Unit tests for config flow and options flow."""

from unittest.mock import MagicMock
import pytest

from custom_components.adaptive_growth_light.config_flow import (
    AdaptiveGrowthLightConfigFlow,
    get_config_schema,
)
from custom_components.adaptive_growth_light.const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
)


def test_config_schema_defaults():
    schema = get_config_schema()
    assert schema is not None


@pytest.mark.asyncio
async def test_config_flow_user_step_creates_entry():
    flow = AdaptiveGrowthLightConfigFlow()
    flow.hass = None

    user_input = {
        CONF_NAME: "Kitchen Basil",
        CONF_TARGET_ENTITY: "switch.kitchen_light",
        CONF_TARGET_PHOTOPERIOD: 15.0,
        CONF_LIGHTING_MODE: "morning",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }

    flow.async_create_entry = MagicMock(
        return_value={"type": "create_entry", "title": user_input[CONF_NAME], "data": user_input}
    )

    result = await flow.async_step_user(user_input)
    assert result["type"] == "create_entry"
    assert result["title"] == "Kitchen Basil"
    assert result["data"] == user_input
