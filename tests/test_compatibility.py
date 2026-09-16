"""Compatibility unit tests for older and newer Home Assistant API variations."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from homeassistant.core import HomeAssistant

from custom_components.adaptive_growth_light import async_setup, FRONTEND_URL
from custom_components.adaptive_growth_light.const import DOMAIN


async def test_legacy_http_register_static_path(hass: HomeAssistant) -> None:
    """Test compatibility with older Home Assistant versions (< 2024.7).

    Older versions only had synchronous `register_static_path` on HomeAssistantHTTP.
    """
    mock_http = MagicMock(spec=["register_static_path"])
    mock_http.register_static_path = MagicMock()
    # Explicitly ensure async_register_static_paths is NOT present
    assert not hasattr(mock_http, "async_register_static_paths")
    hass.http = mock_http

    result = await async_setup(hass, {})
    assert result is True
    mock_http.register_static_path.assert_called_once()
    args, kwargs = mock_http.register_static_path.call_args
    assert args[0] == FRONTEND_URL
    assert kwargs.get("cache_headers") is False


async def test_modern_http_async_register_static_paths(hass: HomeAssistant) -> None:
    """Test compatibility with modern Home Assistant versions (>= 2024.7).

    Modern versions require async `async_register_static_paths([StaticPathConfig(...)])`.
    """
    mock_http = MagicMock(spec=["async_register_static_paths"])
    mock_http.async_register_static_paths = AsyncMock()
    hass.http = mock_http

    result = await async_setup(hass, {})
    assert result is True
    mock_http.async_register_static_paths.assert_awaited_once()


async def test_headless_http_is_none(hass: HomeAssistant) -> None:
    """Test compatibility when HTTP server is not initialized (headless / minimal mode)."""
    hass.http = None

    result = await async_setup(hass, {})
    assert result is True


async def test_static_path_config_import_fallback(hass: HomeAssistant) -> None:
    """Test fallback when StaticPathConfig cannot be imported (legacy versions)."""
    mock_http = MagicMock(spec=["register_static_path"])
    mock_http.register_static_path = MagicMock()
    hass.http = mock_http

    with patch("custom_components.adaptive_growth_light.StaticPathConfig", None):
        result = await async_setup(hass, {})
        assert result is True
        mock_http.register_static_path.assert_called_once()
