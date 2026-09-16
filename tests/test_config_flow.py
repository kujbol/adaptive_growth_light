"""Unit tests for config flow and options flow using pytest-homeassistant-custom-component."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_growth_light.config_flow import get_config_schema
from custom_components.adaptive_growth_light.const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_EARLIEST_START,
    CONF_LATEST_END,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
    DOMAIN,
    MODE_BOTH,
    MODE_EVENING,
    MODE_MORNING,
)


def test_config_schema_defaults():
    schema = get_config_schema()
    assert schema is not None


async def test_config_flow_morning_mode_skips_split(hass: HomeAssistant) -> None:
    """Test that selecting morning mode skips the split slider and goes straight to preview."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    user_input = {
        CONF_NAME: "Kitchen Basil",
        CONF_TARGET_ENTITY: "switch.kitchen_light",
        CONF_TARGET_PHOTOPERIOD: 15.0,
        CONF_LIGHTING_MODE: MODE_MORNING,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }

    # Step 1: Submit configuration -> shows seasonal preview MENU (no split step shown)
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.MENU
    assert result_preview["step_id"] == "preview"
    assert result_preview["menu_options"] == ["confirm", "back"]
    assert "preview_text" in result_preview["description_placeholders"]

    # Step 2: Confirm preview -> creates entry!
    result2 = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kitchen Basil"
    assert result2["data"][CONF_NAME] == "Kitchen Basil"
    assert result2["data"][CONF_TARGET_ENTITY] == "switch.kitchen_light"
    assert result2["data"][CONF_TARGET_PHOTOPERIOD] == 15.0
    assert result2["data"][CONF_LIGHTING_MODE] == MODE_MORNING
    assert result2["data"][CONF_MORNING_SPLIT] == 100.0
    assert result2["data"][CONF_DAYLIGHT_OVERLAP] == 1.0
    # Cut-offs default to None when not specified
    assert result2["data"][CONF_EARLIEST_START] is None
    assert result2["data"][CONF_LATEST_END] is None


async def test_config_flow_both_mode_shows_split_step(hass: HomeAssistant) -> None:
    """Test that selecting both mode shows the split slider before preview."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    user_input = {
        CONF_NAME: "Bedroom Ficus",
        CONF_TARGET_ENTITY: "light.bedroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: MODE_BOTH,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }

    # Step 1: Submit configuration -> shows split step
    result_split = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_split["type"] is FlowResultType.FORM
    assert result_split["step_id"] == "split"

    # Step 2: Configure split percentage -> shows preview menu
    result_preview = await hass.config_entries.flow.async_configure(
        result_split["flow_id"],
        {CONF_MORNING_SPLIT: 40.0},
    )
    assert result_preview["type"] is FlowResultType.MENU
    assert result_preview["step_id"] == "preview"

    # Step 3: Confirm -> creates entry with configured split
    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["data"][CONF_MORNING_SPLIT] == 40.0


async def test_config_flow_evening_mode_auto_split(hass: HomeAssistant) -> None:
    """Test that evening mode sets split to 0.0 and skips split step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    user_input = {
        CONF_NAME: "Evening Fern",
        CONF_TARGET_ENTITY: "light.fern",
        CONF_TARGET_PHOTOPERIOD: 12.0,
        CONF_LIGHTING_MODE: MODE_EVENING,
        CONF_DAYLIGHT_OVERLAP: 0.5,
    }
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.MENU
    assert result_preview["step_id"] == "preview"

    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["data"][CONF_MORNING_SPLIT] == 0.0


async def test_config_flow_back_button_from_preview(hass: HomeAssistant) -> None:
    """Test navigating back from preview to adjust settings without losing input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    user_input = {
        CONF_NAME: "Office Monster",
        CONF_TARGET_ENTITY: "switch.office_lamp",
        CONF_TARGET_PHOTOPERIOD: 13.0,
        CONF_LIGHTING_MODE: MODE_MORNING,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.MENU
    assert result_preview["step_id"] == "preview"

    # User clicks 'back' to change settings
    result_back = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "back"},
    )
    assert result_back["type"] is FlowResultType.FORM
    assert result_back["step_id"] == "user"

    # User changes target photoperiod to 16.0
    updated_input = {
        **user_input,
        CONF_TARGET_PHOTOPERIOD: 16.0,
    }
    result_preview2 = await hass.config_entries.flow.async_configure(
        result_back["flow_id"],
        updated_input,
    )
    assert result_preview2["type"] is FlowResultType.MENU

    # Confirm
    result_create = await hass.config_entries.flow.async_configure(
        result_preview2["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["data"][CONF_TARGET_PHOTOPERIOD] == 16.0


async def test_config_flow_custom_cutoffs(hass: HomeAssistant) -> None:
    """Test specifying custom cut-offs in config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    user_input = {
        CONF_NAME: "Bedroom Ficus",
        CONF_TARGET_ENTITY: "light.bedroom_grow_light",
        CONF_TARGET_PHOTOPERIOD: 14.0,
        CONF_LIGHTING_MODE: MODE_EVENING,
        CONF_DAYLIGHT_OVERLAP: 1.0,
        CONF_EARLIEST_START: "07:00:00",
        CONF_LATEST_END: "21:30:00",
    }
    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.MENU

    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["data"][CONF_EARLIEST_START] == "07:00:00"
    assert result_create["data"][CONF_LATEST_END] == "21:30:00"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow to update settings with seasonal preview and confirm."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Balcony Mint",
        data={
            CONF_NAME: "Balcony Mint",
            CONF_TARGET_ENTITY: "switch.mint_light",
            CONF_TARGET_PHOTOPERIOD: 12.0,
            CONF_LIGHTING_MODE: MODE_BOTH,
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 1.0,
            CONF_EARLIEST_START: None,
            CONF_LATEST_END: None,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Step 1: Submit options -> mode is evening, so goes to preview menu
    result_preview = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Balcony Mint Updated",
            CONF_TARGET_ENTITY: "switch.mint_light_new",
            CONF_TARGET_PHOTOPERIOD: 14.5,
            CONF_LIGHTING_MODE: MODE_EVENING,
            CONF_DAYLIGHT_OVERLAP: 1.5,
        },
    )
    assert result_preview["type"] is FlowResultType.MENU
    assert result_preview["step_id"] == "preview"

    # Step 2: Confirm preview -> updates entry
    result2 = await hass.config_entries.options.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_TARGET_PHOTOPERIOD] == 14.5
    assert entry.data[CONF_LIGHTING_MODE] == MODE_EVENING
    assert entry.data[CONF_DAYLIGHT_OVERLAP] == 1.5


async def test_options_flow_back_navigation(hass: HomeAssistant) -> None:
    """Test navigating back in options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Balcony Mint",
        data={
            CONF_NAME: "Balcony Mint",
            CONF_TARGET_ENTITY: "switch.mint_light",
            CONF_TARGET_PHOTOPERIOD: 12.0,
            CONF_LIGHTING_MODE: MODE_MORNING,
            CONF_MORNING_SPLIT: 100.0,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result_preview = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Balcony Mint",
            CONF_TARGET_ENTITY: "switch.mint_light",
            CONF_TARGET_PHOTOPERIOD: 14.0,
            CONF_LIGHTING_MODE: MODE_MORNING,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    assert result_preview["type"] is FlowResultType.MENU

    # Click back
    result_back = await hass.config_entries.options.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "back"},
    )
    assert result_back["type"] is FlowResultType.FORM
    assert result_back["step_id"] == "init"


async def test_config_flow_auto_name_from_entity(hass: HomeAssistant) -> None:
    """Test that omitting name automatically derives a clean default name from target entity."""
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
        CONF_LIGHTING_MODE: MODE_EVENING,
        CONF_DAYLIGHT_OVERLAP: 1.0,
    }

    result_preview = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result_preview["type"] is FlowResultType.MENU
    assert result_preview["step_id"] == "preview"

    # Confirm preview
    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
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
            CONF_LIGHTING_MODE: MODE_EVENING,
            CONF_DAYLIGHT_OVERLAP: 0.5,
        },
    )
    result_create = await hass.config_entries.flow.async_configure(
        result_preview["flow_id"],
        {"next_step_id": "confirm"},
    )
    assert result_create["type"] is FlowResultType.CREATE_ENTRY
    assert result_create["title"] == "Kitchen Grow Adaptive Light"


async def test_config_flow_mode_switch_from_morning_to_both_shows_split_slider(
    hass: HomeAssistant,
) -> None:
    """Test that switching from morning mode back to both mode always shows the split slider."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    # 1. User initially picks Morning
    res_morn = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Ficus",
            CONF_TARGET_ENTITY: "switch.ficus",
            CONF_TARGET_PHOTOPERIOD: 14.0,
            CONF_LIGHTING_MODE: MODE_MORNING,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    assert res_morn["type"] is FlowResultType.MENU
    assert res_morn["step_id"] == "preview"

    # 2. User clicks back to change mode to Both
    res_back = await hass.config_entries.flow.async_configure(
        res_morn["flow_id"],
        {"next_step_id": "back"},
    )
    assert res_back["type"] is FlowResultType.FORM
    assert res_back["step_id"] == "user"

    # 3. User switches to Both
    res_both = await hass.config_entries.flow.async_configure(
        res_back["flow_id"],
        {
            CONF_NAME: "Ficus",
            CONF_TARGET_ENTITY: "switch.ficus",
            CONF_TARGET_PHOTOPERIOD: 14.0,
            CONF_LIGHTING_MODE: MODE_BOTH,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    # Must show the split slider!
    assert res_both["type"] is FlowResultType.FORM
    assert res_both["step_id"] == "split"
