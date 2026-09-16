"""Mock Home Assistant modules for standalone testing."""

from datetime import datetime, timezone
import sys
import types
from unittest.mock import MagicMock
import zoneinfo

# Root package
ha_pkg = types.ModuleType("homeassistant")
sys.modules["homeassistant"] = ha_pkg

# Submodules
class MockConfigFlow:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def async_create_entry(self, title: str, data: dict):
        return {"type": "create_entry", "title": title, "data": data}

    def async_show_form(self, step_id: str, data_schema=None, errors=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}

class MockOptionsFlow:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

config_entries_mock = MagicMock()
config_entries_mock.ConfigFlow = MockConfigFlow
config_entries_mock.OptionsFlow = MockOptionsFlow
sys.modules["homeassistant.config_entries"] = config_entries_mock

sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
sys.modules["homeassistant.helpers.event"] = MagicMock()
sys.modules["homeassistant.helpers.selector"] = MagicMock()

# homeassistant.util and homeassistant.util.dt
ha_util = types.ModuleType("homeassistant.util")
dt_module = types.ModuleType("homeassistant.util.dt")
utc_tz = zoneinfo.ZoneInfo("UTC")
dt_module.DEFAULT_TIME_ZONE = utc_tz
dt_module.now = lambda: datetime.now(utc_tz)
dt_module.utcnow = lambda: datetime.now(timezone.utc)

ha_util.dt = dt_module
sys.modules["homeassistant.util"] = ha_util
sys.modules["homeassistant.util.dt"] = dt_module

sys.modules["homeassistant.components"] = MagicMock()
sys.modules["homeassistant.components.switch"] = MagicMock()
sys.modules["homeassistant.components.sensor"] = MagicMock()
sys.modules["homeassistant.components.number"] = MagicMock()
sys.modules["homeassistant.components.select"] = MagicMock()

# Voluptuous mock for Home Assistant schema building
vol_mock = MagicMock()
vol_mock.Schema = MagicMock(return_value=MagicMock())
vol_mock.Required = MagicMock(side_effect=lambda k, default=None: k)
vol_mock.Optional = MagicMock(side_effect=lambda k, default=None: k)
sys.modules["voluptuous"] = vol_mock
