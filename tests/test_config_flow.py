"""Unit tests for config flow and options flow using pytest-homeassistant-custom-component."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_growth_light.config_flow import get_config_schema
from custom_components.adaptive_growth_light.const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
    DOMAIN,
)


def test_config_schema_defaults():
    schema = get_config_schema()
    assert schema is not None


async def test_config_flow_user_step_creates_entry(hass: HomeAssistant) -> None:
    """Test user step of config flow leading to seasonal preview and entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    user_input = {
        CONF_NAME: "Kitchen Basil",
        CONF_TARGET_ENTITY: "switch.kitchen_light",
        CONF_TARGET_PHOTOPERIOD: 15.0,
        CONF_LIGHTING_MODE: "morning",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }

    # Step 1: Submit configuration -> shows seasonal preview step!
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.FORM
    assert result_preview["step_id"] == "preview"
    assert "preview_text" in result_preview["description_placeholders"]

    # Step 2: Confirm preview -> creates entry!
    result2 = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kitchen Basil"
    assert result2["data"] == user_input


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow to update settings with seasonal preview."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Balcony Mint",
        data={
            CONF_NAME: "Balcony Mint",
            CONF_TARGET_ENTITY: "switch.mint_light",
            CONF_TARGET_PHOTOPERIOD: 12.0,
            CONF_LIGHTING_MODE: "both",
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Step 1: Submit options -> shows seasonal preview step
    result_preview = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Balcony Mint Updated",
            CONF_TARGET_ENTITY: "switch.mint_light_new",
            CONF_TARGET_PHOTOPERIOD: 14.5,
            CONF_LIGHTING_MODE: "evening",
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 1.5,
        },
    )
    assert result_preview["type"] is FlowResultType.FORM
    assert result_preview["step_id"] == "preview"

    # Step 2: Confirm preview -> updates entry
    result2 = await hass.config_entries.options.async_configure(
        result_preview["flow_id"],
        {},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_TARGET_PHOTOPERIOD] == 14.5
    assert entry.data[CONF_LIGHTING_MODE] == "evening"
    assert entry.data[CONF_DAYLIGHT_OVERLAP] == 1.5
