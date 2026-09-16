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

    # Verify new time cut-off entities (default to unknown when no cut-off set)
    earliest_time = hass.states.get("time.bathroom_grow_light_earliest_morning_start")
    assert earliest_time is not None
    assert earliest_time.state == "unknown"

    latest_time = hass.states.get("time.bathroom_grow_light_latest_evening_end")
    assert latest_time is not None
    assert latest_time.state == "unknown"

    # Verify setting a cut-off time dynamically updates the entity
    await hass.services.async_call(
        "time",
        "set_value",
        {"entity_id": "time.bathroom_grow_light_earliest_morning_start", "time": "06:30:00"},
        blocking=True,
    )
    earliest_time = hass.states.get("time.bathroom_grow_light_earliest_morning_start")
    assert earliest_time.state == "06:30:00"

    # Verify earliest turn on sensor
    earliest_turn_on = hass.states.get("sensor.bathroom_grow_light_earliest_turn_on_of_year")
    assert earliest_turn_on is not None
    assert "effective_time" in earliest_turn_on.attributes

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


async def test_auto_register_frontend_resource(hass: HomeAssistant) -> None:
    """Verify that frontend extra_js_url is auto-registered."""
    from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
    from custom_components.adaptive_growth_light import async_register_frontend
    from custom_components.adaptive_growth_light.const import FRONTEND_URL, DOMAIN

    # Reset registration flag
    hass.data.pop(f"{DOMAIN}_frontend_registered", None)
    hass.config.components.add("frontend")
    hass.data[DATA_EXTRA_MODULE_URL] = set()

    await async_register_frontend(hass)

    assert FRONTEND_URL in hass.data[DATA_EXTRA_MODULE_URL]


def test_brand_assets_validity() -> None:
    """Verify that all Home Assistant brand icons and logos exist with valid PNG format and dimensions."""
    from pathlib import Path
    from PIL import Image

    root = Path(__file__).parent.parent
    brand_dir = root / "custom_components" / "adaptive_growth_light" / "brand"
    assert brand_dir.is_dir(), "brand/ directory must exist in custom component"

    expected_assets = {
        brand_dir / "icon.png": (256, 256),
        brand_dir / "icon@2x.png": (512, 512),
        brand_dir / "dark_icon.png": (256, 256),
        brand_dir / "dark_icon@2x.png": (512, 512),
        brand_dir / "logo.png": (512, 512),
        brand_dir / "logo@2x.png": (1024, 1024),
        brand_dir / "dark_logo.png": (512, 512),
        brand_dir / "dark_logo@2x.png": (1024, 1024),
        root / "custom_components" / "adaptive_growth_light" / "icon.png": (256, 256),
        root / "custom_components" / "adaptive_growth_light" / "logo.png": (512, 512),
        root / "icon.png": (256, 256),
        root / "icon@2x.png": (512, 512),
        root / "logo.png": (512, 512),
        root / "images" / "icon.png": (256, 256),
        root / "images" / "logo.png": (1024, 1024),
    }

    png_magic_bytes = b"\x89PNG\r\n\x1a\n"

    for path, (expected_w, expected_h) in expected_assets.items():
        assert path.exists(), f"Asset missing: {path}"
        assert path.stat().st_size > 0, f"Asset empty: {path}"

        with open(path, "rb") as fp:
            header = fp.read(8)
            assert header == png_magic_bytes, f"File {path.name} is not a valid PNG!"

        with Image.open(path) as img:
            assert img.format == "PNG", f"{path.name} PIL format is not PNG"
            assert img.size == (expected_w, expected_h), f"{path.name} size mismatch: got {img.size}, expected {(expected_w, expected_h)}"
            assert img.mode == "RGBA", f"{path.name} must have RGBA alpha transparency channel"


def test_card_visual_editor_definition() -> None:
    """Verify that adaptive-growth-light-card.js registers a visual card editor with entity filtering."""
    from pathlib import Path

    card_js_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "adaptive_growth_light"
        / "frontend"
        / "adaptive-growth-light-card.js"
    )
    assert card_js_path.exists(), "adaptive-growth-light-card.js must exist"

    content = card_js_path.read_text(encoding="utf-8")

    # Verify static methods on AdaptiveGrowthLightCard
    assert "static getConfigElement()" in content, "Card must implement static getConfigElement for visual editor"
    assert "adaptive-growth-light-card-editor" in content, "Card must instantiate adaptive-growth-light-card-editor"
    assert "static getStubConfig(hass)" in content, "Card must implement static getStubConfig for smart entity preselection"

    # Verify Editor class and registration
    assert "class AdaptiveGrowthLightCardEditor extends HTMLElement" in content
    assert 'customElements.define("adaptive-growth-light-card-editor", AdaptiveGrowthLightCardEditor)' in content

    # Verify entity filtering for adaptive growth light
    assert 'integration: "adaptive_growth_light"' in content, "Editor must filter entities by adaptive_growth_light integration"
    assert "_getDiscoveredEntities()" in content, "Editor must provide quick-select for discovered adaptive lights"
    assert "Discovered Adaptive Lights" in content

    # Verify compact tile mode and interactive modal dialog
    assert "compact-tile" in content, "Card must support compact tile view"
    assert "modal-backdrop" in content, "Card must include modal backdrop"
    assert "modal-dialog" in content, "Card must include modal popup dialog"
    assert "_openModal" in content, "Card must include modal open handler"
    assert "_closeModal" in content, "Card must include modal close handler"


async def test_switch_attributes_and_non_blocking_coordinator(hass: HomeAssistant) -> None:
    """Verify master switch attributes populate photoperiod metrics and coordinator avoids blocking open()."""
    from unittest.mock import patch
    from custom_components.adaptive_growth_light.coordinator import AdaptiveGrowthLightCoordinator

    # Ensure coordinator __init__ does not call open()
    with patch("builtins.open") as mock_open:
        coord = AdaptiveGrowthLightCoordinator(
            hass,
            "test_entry",
            {
                CONF_NAME: "Plant Light",
                CONF_TARGET_ENTITY: "switch.dummy_light",
                CONF_TARGET_PHOTOPERIOD: 14.0,
            },
            sw_version="1.1.6",
        )
        assert mock_open.call_count == 0, "Coordinator __init__ must never perform blocking file open"
        assert coord.sw_version == "1.1.6"

    # Setup integration with real switch
    await hass.config.async_set_time_zone("Europe/Warsaw")
    await hass.config.async_update(latitude=52.2297, longitude=21.0122, elevation=100)
    hass.states.async_set("switch.flower_light", "off")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Flower Light",
        data={
            CONF_NAME: "Flower Light",
            CONF_TARGET_ENTITY: "switch.flower_light",
            CONF_TARGET_PHOTOPERIOD: 14.0,
            CONF_LIGHTING_MODE: "both",
            CONF_MORNING_SPLIT: 50.0,
            CONF_DAYLIGHT_OVERLAP: 1.0,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    switch = hass.states.get("switch.flower_light_automation")
    assert switch is not None
    attrs = switch.attributes

    # Check that extra_state_attributes contain all timeline and metric data needed by the card
    assert "supplementary_hours" in attrs
    assert "natural_daylight_hours" in attrs
    assert "earliest_turn_on" in attrs
    assert "today_morning_start" in attrs
    assert "today_morning_end" in attrs
    assert "today_evening_start" in attrs
    assert "today_evening_end" in attrs
    assert "seasonal_months" in attrs
    assert len(attrs["seasonal_months"]) == 12

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()



