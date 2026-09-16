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
    assert result2["data"][CONF_NAME] == "Kitchen Basil"
    assert result2["data"][CONF_TARGET_ENTITY] == "switch.kitchen_light"
    assert result2["data"][CONF_TARGET_PHOTOPERIOD] == 15.0
    assert result2["data"][CONF_LIGHTING_MODE] == "morning"
    assert result2["data"][CONF_MORNING_SPLIT] == 50.0
    assert result2["data"][CONF_DAYLIGHT_OVERLAP] == 1.0
    assert result2["data"]["earliest_start"] == "06:30:00"
    assert result2["data"]["latest_end"] == "22:00:00"


async def test_config_flow_custom_cutoffs_in_preview(hass: HomeAssistant) -> None:
    """Test modifying cut-offs and photoperiod during preview step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    user_input = {
        CONF_NAME: "Bedroom Ficus",
        CONF_TARGET_ENTITY: "light.bedroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
        "earliest_start": "06:30:00",
        "latest_end": "22:00:00",
    }
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.FORM
    assert result_preview["step_id"] == "preview"

    # User tweaks earliest_start to 07:00:00 in the preview step before confirming!
    result2 = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {
            CONF_NAME: "Bedroom Ficus",
            CONF_TARGET_PHOTOPERIOD: 13.5,
            "earliest_start": "07:00:00",
            "latest_end": "21:30:00",
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"]["earliest_start"] == "07:00:00"
    assert result2["data"]["latest_end"] == "21:30:00"
    assert result2["data"][CONF_TARGET_PHOTOPERIOD] == 13.5


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


async def test_config_flow_auto_name_from_entity(hass: HomeAssistant) -> None:
    """Test that omitting name automatically derives a clean default name from target entity."""
    # Pre-register state with friendly name
    hass.states.async_set(
        "light.living_room_ficus", "off", {"friendly_name": "Living Room Ficus"}
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM

    # User does NOT provide CONF_NAME
    user_input = {
        CONF_TARGET_ENTITY: "light.living_room_ficus",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: "both",
        CONF_MORNING_SPLIT: 50.0,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }

    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.FORM
    assert result_preview["step_id"] == "preview"

    # Confirm preview without editing name
    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["title"] == "Living Room Ficus Adaptive Light"
    assert result_create["data"][CONF_NAME] == "Living Room Ficus Adaptive Light"


async def test_config_flow_auto_name_entity_ending_with_light(
    hass: HomeAssistant,
) -> None:
    """Test that entities ending with 'Light' don't get redundant 'Light' appended."""
    hass.states.async_set(
        "light.kitchen_grow_light", "off", {"friendly_name": "Kitchen Grow Light"}
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TARGET_ENTITY: "light.kitchen_grow_light",
            CONF_TARGET_PHOTOPERIOD: 13.0,
            CONF_LIGHTING_MODE: "evening",
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 0.5,
        },
    )
    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["title"] == "Kitchen Grow Adaptive Light"


async def test_config_flow_preview_allows_overriding_auto_name(
    hass: HomeAssistant,
) -> None:
    """Test that the user can override the automatically derived name during the preview step."""
    hass.states.async_set(
        "switch.shelf_plug", "off", {"friendly_name": "Shelf Plug"}
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TARGET_ENTITY: "switch.shelf_plug",
            CONF_TARGET_PHOTOPERIOD: 14.0,
            CONF_LIGHTING_MODE: "morning",
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    # In preview step, user changes name to "My Custom Herb Lamp"
    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {CONF_NAME: "My Custom Herb Lamp"},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["title"] == "My Custom Herb Lamp"
    assert result_create["data"][CONF_NAME] == "My Custom Herb Lamp"

