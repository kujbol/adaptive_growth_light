"""Config flow and options flow for Adaptive Growth Light."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DAYLIGHT_OVERLAP,
    CONF_EARLIEST_START,
    CONF_LATEST_END,
    CONF_LIGHTING_MODE,
    CONF_MORNING_SPLIT,
    CONF_NAME,
    CONF_TARGET_ENTITY,
    CONF_TARGET_PHOTOPERIOD,
    DEFAULT_DAYLIGHT_OVERLAP,
    DEFAULT_EARLIEST_START,
    DEFAULT_LATEST_END,
    DEFAULT_LIGHTING_MODE,
    DEFAULT_MORNING_SPLIT,
    DEFAULT_NAME,
    DEFAULT_TARGET_PHOTOPERIOD,
    DOMAIN,
    LIGHTING_MODES,
    MAX_OVERLAP,
    MAX_PHOTOPERIOD,
    MAX_SPLIT,
    MIN_OVERLAP,
    MIN_PHOTOPERIOD,
    MIN_SPLIT,
    MODE_BOTH,
    MODE_EVENING,
    MODE_MORNING,
    STEP_OVERLAP,
    STEP_PHOTOPERIOD,
    STEP_SPLIT,
)
from .solar import SolarCalculator


def generate_default_name_from_entity(hass: HomeAssistant, entity_id: str) -> str:
    """Generate a clean default adaptive light name based on the selected entity."""
    if not entity_id:
        return DEFAULT_NAME

    entity_name = ""
    state = hass.states.get(entity_id)
    if state and state.name:
        entity_name = state.name
    else:
        try:
            from homeassistant.helpers import entity_registry as er

            ent_reg = er.async_get(hass)
            entry = ent_reg.async_get(entity_id)
            if entry:
                entity_name = entry.name or entry.original_name or ""
        except Exception:
            pass

    if not entity_name:
        object_id = entity_id.split(".", 1)[-1]
        entity_name = object_id.replace("_", " ").title()

    clean = entity_name.strip()
    if not clean:
        return DEFAULT_NAME
    if "adaptive" in clean.lower():
        return clean
    if clean.lower() == "light":
        return "Adaptive Light"
    if clean.lower().endswith(" light"):
        base = clean[:-6].strip()
        return f"{base} Adaptive Light"
    return f"{clean} Adaptive Light"


def get_config_schema(
    defaults: dict[str, Any] | None = None,
    include_split: bool = False,
) -> vol.Schema:
    """Generate the config schema with current or default values."""
    defaults = defaults or {}

    schema_dict: dict[Any, Any] = {}

    # Target entity selection
    if defaults.get(CONF_TARGET_ENTITY):
        schema_dict[
            vol.Required(
                CONF_TARGET_ENTITY,
                default=defaults[CONF_TARGET_ENTITY],
            )
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["switch", "light"])
        )
    else:
        schema_dict[
            vol.Required(CONF_TARGET_ENTITY)
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["switch", "light"])
        )

    # Name is optional: if left blank, it will be automatically derived from the target entity
    if defaults.get(CONF_NAME):
        schema_dict[
            vol.Optional(
                CONF_NAME,
                default=defaults[CONF_NAME],
            )
        ] = selector.TextSelector()
    else:
        schema_dict[vol.Optional(CONF_NAME)] = selector.TextSelector()

    schema_dict[
        vol.Required(
            CONF_TARGET_PHOTOPERIOD,
            default=float(defaults.get(CONF_TARGET_PHOTOPERIOD, DEFAULT_TARGET_PHOTOPERIOD)),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_PHOTOPERIOD,
            max=MAX_PHOTOPERIOD,
            step=STEP_PHOTOPERIOD,
            unit_of_measurement="h",
            mode=selector.NumberSelectorMode.SLIDER,
        )
    )

    schema_dict[
        vol.Required(
            CONF_LIGHTING_MODE,
            default=defaults.get(CONF_LIGHTING_MODE, DEFAULT_LIGHTING_MODE),
        )
    ] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=LIGHTING_MODES,
            mode=selector.SelectSelectorMode.DROPDOWN,
            translation_key="lighting_mode",
        )
    )

    # Morning split percentage is only included when mode is "both"
    if include_split:
        schema_dict[
            vol.Required(
                CONF_MORNING_SPLIT,
                default=float(defaults.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT)),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_SPLIT,
                max=MAX_SPLIT,
                step=STEP_SPLIT,
                unit_of_measurement="%",
                mode=selector.NumberSelectorMode.SLIDER,
            )
        )

    schema_dict[
        vol.Required(
            CONF_DAYLIGHT_OVERLAP,
            default=float(defaults.get(CONF_DAYLIGHT_OVERLAP, DEFAULT_DAYLIGHT_OVERLAP)),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=MIN_OVERLAP,
            max=MAX_OVERLAP,
            step=STEP_OVERLAP,
            unit_of_measurement="h",
            mode=selector.NumberSelectorMode.SLIDER,
        )
    )

    # Cut-offs: optional without default so user can choose to have no cut-off
    if defaults.get(CONF_EARLIEST_START):
        schema_dict[
            vol.Optional(
                CONF_EARLIEST_START,
                default=str(defaults[CONF_EARLIEST_START]),
            )
        ] = selector.TimeSelector()
    else:
        schema_dict[vol.Optional(CONF_EARLIEST_START)] = selector.TimeSelector()

    if defaults.get(CONF_LATEST_END):
        schema_dict[
            vol.Optional(
                CONF_LATEST_END,
                default=str(defaults[CONF_LATEST_END]),
            )
        ] = selector.TimeSelector()
    else:
        schema_dict[vol.Optional(CONF_LATEST_END)] = selector.TimeSelector()

    return vol.Schema(schema_dict)


class AdaptiveGrowthLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Adaptive Growth Light."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._config_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial configuration step."""
        if user_input is not None:
            custom_name = (user_input.get(CONF_NAME) or "").strip()
            if not custom_name:
                custom_name = generate_default_name_from_entity(
                    self.hass, user_input.get(CONF_TARGET_ENTITY, "")
                )
            user_input[CONF_NAME] = custom_name

            # Normalize empty cut-offs to None
            if not user_input.get(CONF_EARLIEST_START):
                user_input[CONF_EARLIEST_START] = None
            if not user_input.get(CONF_LATEST_END):
                user_input[CONF_LATEST_END] = None

            self._config_data.update(user_input)

            # Route based on lighting mode
            mode = user_input.get(CONF_LIGHTING_MODE, DEFAULT_LIGHTING_MODE)
            if mode == MODE_MORNING:
                self._config_data[CONF_MORNING_SPLIT] = 100.0
                return await self.async_step_preview()
            elif mode == MODE_EVENING:
                self._config_data[CONF_MORNING_SPLIT] = 0.0
                return await self.async_step_preview()
            else:  # MODE_BOTH
                return await self.async_step_split()

        return self.async_show_form(
            step_id="user",
            data_schema=get_config_schema(self._config_data, include_split=False),
        )

    async def async_step_split(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure morning/evening split for Both mode."""
        if user_input is not None:
            self._config_data.update(user_input)
            return await self.async_step_preview()

        split_val = self._config_data.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT)
        if split_val in (0.0, 100.0):
            split_val = DEFAULT_MORNING_SPLIT

        split_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MORNING_SPLIT,
                    default=float(split_val),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SPLIT,
                        max=MAX_SPLIT,
                        step=STEP_SPLIT,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="split",
            data_schema=split_schema,
        )

    async def async_step_preview(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Display seasonal daylight vs. supplementary light preview with confirm & back navigation."""
        calc = SolarCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            elevation=self.hass.config.elevation,
            tz=dt_util.DEFAULT_TIME_ZONE,
        )
        preview_text = calc.get_seasonal_preview_text(
            target_hours=self._config_data[CONF_TARGET_PHOTOPERIOD],
            mode=self._config_data[CONF_LIGHTING_MODE],
            morning_split_pct=self._config_data.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT),
            overlap_hours=self._config_data[CONF_DAYLIGHT_OVERLAP],
            earliest_start=self._config_data.get(CONF_EARLIEST_START),
            latest_end=self._config_data.get(CONF_LATEST_END),
        )

        return self.async_show_menu(
            step_id="preview",
            menu_options=["confirm", "back"],
            description_placeholders={
                "preview_text": preview_text,
                "target_hours": str(self._config_data[CONF_TARGET_PHOTOPERIOD]),
            },
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Create entry when confirmed from preview."""
        name = self._config_data.get(CONF_NAME) or generate_default_name_from_entity(
            self.hass, self._config_data.get(CONF_TARGET_ENTITY, "")
        )
        self._config_data[CONF_NAME] = name
        return self.async_create_entry(title=name, data=self._config_data)

    async def async_step_back(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Navigate back to user configuration step with existing values preserved."""
        return self.async_show_form(
            step_id="user",
            data_schema=get_config_schema(self._config_data, include_split=False),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler for this entry."""
        return AdaptiveGrowthLightOptionsFlowHandler()


class AdaptiveGrowthLightOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for an existing config entry."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._options_data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage configuration options."""
        if user_input is not None:
            custom_name = (user_input.get(CONF_NAME) or "").strip()
            if not custom_name:
                custom_name = generate_default_name_from_entity(
                    self.hass, user_input.get(CONF_TARGET_ENTITY, "")
                )
            user_input[CONF_NAME] = custom_name

            if not user_input.get(CONF_EARLIEST_START):
                user_input[CONF_EARLIEST_START] = None
            if not user_input.get(CONF_LATEST_END):
                user_input[CONF_LATEST_END] = None

            self._options_data.update(user_input)

            mode = user_input.get(CONF_LIGHTING_MODE, DEFAULT_LIGHTING_MODE)
            if mode == MODE_MORNING:
                self._options_data[CONF_MORNING_SPLIT] = 100.0
                return await self.async_step_preview()
            elif mode == MODE_EVENING:
                self._options_data[CONF_MORNING_SPLIT] = 0.0
                return await self.async_step_preview()
            else:  # MODE_BOTH
                return await self.async_step_split()

        current_data = {**self.config_entry.data, **self.config_entry.options, **self._options_data}
        return self.async_show_form(
            step_id="init",
            data_schema=get_config_schema(current_data, include_split=False),
        )

    async def async_step_split(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure morning/evening split for Both mode in options."""
        if user_input is not None:
            self._options_data.update(user_input)
            return await self.async_step_preview()

        current_split = self._options_data.get(
            CONF_MORNING_SPLIT,
            self.config_entry.data.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT),
        )
        if current_split in (0.0, 100.0):
            current_split = DEFAULT_MORNING_SPLIT

        split_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MORNING_SPLIT,
                    default=float(current_split),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SPLIT,
                        max=MAX_SPLIT,
                        step=STEP_SPLIT,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="split",
            data_schema=split_schema,
        )

    async def async_step_preview(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Display seasonal preview with confirm & back navigation."""
        calc = SolarCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            elevation=self.hass.config.elevation,
            tz=dt_util.DEFAULT_TIME_ZONE,
        )
        current_data = {**self.config_entry.data, **self.config_entry.options, **self._options_data}
        preview_text = calc.get_seasonal_preview_text(
            target_hours=current_data[CONF_TARGET_PHOTOPERIOD],
            mode=current_data[CONF_LIGHTING_MODE],
            morning_split_pct=current_data.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT),
            overlap_hours=current_data[CONF_DAYLIGHT_OVERLAP],
            earliest_start=current_data.get(CONF_EARLIEST_START),
            latest_end=current_data.get(CONF_LATEST_END),
        )

        return self.async_show_menu(
            step_id="preview",
            menu_options=["confirm", "back"],
            description_placeholders={
                "preview_text": preview_text,
                "target_hours": str(current_data[CONF_TARGET_PHOTOPERIOD]),
            },
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Save options when confirmed."""
        name = self._options_data.get(CONF_NAME) or self.config_entry.title
        self._options_data[CONF_NAME] = name

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            title=name,
            data={**self.config_entry.data, **self._options_data},
        )
        return self.async_create_entry(title="", data=self._options_data)

    async def async_step_back(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Navigate back to init step."""
        current_data = {**self.config_entry.data, **self.config_entry.options, **self._options_data}
        return self.async_show_form(
            step_id="init",
            data_schema=get_config_schema(current_data, include_split=False),
        )


