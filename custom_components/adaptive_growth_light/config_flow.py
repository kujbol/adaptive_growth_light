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


def get_config_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
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

    schema_dict.update(
        {
            vol.Required(
                CONF_TARGET_PHOTOPERIOD,
                default=float(defaults.get(CONF_TARGET_PHOTOPERIOD, DEFAULT_TARGET_PHOTOPERIOD)),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_PHOTOPERIOD,
                    max=MAX_PHOTOPERIOD,
                    step=STEP_PHOTOPERIOD,
                    unit_of_measurement="h",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Required(
                CONF_LIGHTING_MODE,
                default=defaults.get(CONF_LIGHTING_MODE, DEFAULT_LIGHTING_MODE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=LIGHTING_MODES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="lighting_mode",
                )
            ),
            vol.Required(
                CONF_MORNING_SPLIT,
                default=float(defaults.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT)),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_SPLIT,
                    max=MAX_SPLIT,
                    step=STEP_SPLIT,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Required(
                CONF_DAYLIGHT_OVERLAP,
                default=float(defaults.get(CONF_DAYLIGHT_OVERLAP, DEFAULT_DAYLIGHT_OVERLAP)),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_OVERLAP,
                    max=MAX_OVERLAP,
                    step=STEP_OVERLAP,
                    unit_of_measurement="h",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Optional(
                CONF_EARLIEST_START,
                default=str(defaults.get(CONF_EARLIEST_START, DEFAULT_EARLIEST_START)),
            ): selector.TimeSelector(),
            vol.Optional(
                CONF_LATEST_END,
                default=str(defaults.get(CONF_LATEST_END, DEFAULT_LATEST_END)),
            ): selector.TimeSelector(),
        }
    )
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
        """Handle the initial step."""
        if user_input is not None:
            # If user didn't specify a name, auto-derive it from the selected entity
            custom_name = (user_input.get(CONF_NAME) or "").strip()
            if not custom_name:
                custom_name = generate_default_name_from_entity(
                    self.hass, user_input.get(CONF_TARGET_ENTITY, "")
                )
            user_input[CONF_NAME] = custom_name

            self._config_data = user_input
            return await self.async_step_preview()

        return self.async_show_form(
            step_id="user",
            data_schema=get_config_schema(),
        )

    async def async_step_preview(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Display seasonal daylight vs. supplementary light preview before creating entry."""
        if user_input is not None:
            self._config_data.update(user_input)
            preview_name = (user_input.get(CONF_NAME) or "").strip()
            if not preview_name:
                preview_name = generate_default_name_from_entity(
                    self.hass, self._config_data.get(CONF_TARGET_ENTITY, "")
                )
            self._config_data[CONF_NAME] = preview_name
            return self.async_create_entry(title=preview_name, data=self._config_data)

        calc = SolarCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            elevation=self.hass.config.elevation,
            tz=dt_util.DEFAULT_TIME_ZONE,
        )
        preview_text = calc.get_seasonal_preview_text(
            target_hours=self._config_data[CONF_TARGET_PHOTOPERIOD],
            mode=self._config_data[CONF_LIGHTING_MODE],
            morning_split_pct=self._config_data[CONF_MORNING_SPLIT],
            overlap_hours=self._config_data[CONF_DAYLIGHT_OVERLAP],
            earliest_start=self._config_data.get(CONF_EARLIEST_START, DEFAULT_EARLIEST_START),
            latest_end=self._config_data.get(CONF_LATEST_END, DEFAULT_LATEST_END),
        )

        current_name = self._config_data.get(CONF_NAME) or generate_default_name_from_entity(
            self.hass, self._config_data.get(CONF_TARGET_ENTITY, "")
        )
        self._config_data[CONF_NAME] = current_name

        preview_schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=current_name,
                ): selector.TextSelector(),
                vol.Required(
                    CONF_TARGET_PHOTOPERIOD,
                    default=float(self._config_data.get(CONF_TARGET_PHOTOPERIOD, DEFAULT_TARGET_PHOTOPERIOD)),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_PHOTOPERIOD,
                        max=MAX_PHOTOPERIOD,
                        step=STEP_PHOTOPERIOD,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_EARLIEST_START,
                    default=str(self._config_data.get(CONF_EARLIEST_START, DEFAULT_EARLIEST_START)),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_LATEST_END,
                    default=str(self._config_data.get(CONF_LATEST_END, DEFAULT_LATEST_END)),
                ): selector.TimeSelector(),
            }
        )

        return self.async_show_form(
            step_id="preview",
            data_schema=preview_schema,
            description_placeholders={
                "preview_text": preview_text,
                "target_hours": str(self._config_data[CONF_TARGET_PHOTOPERIOD]),
            },
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
            self._options_data = user_input
            return await self.async_step_preview()

        current_data = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=get_config_schema(current_data),
        )

    async def async_step_preview(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Display seasonal preview before saving updated settings."""
        if user_input is not None:
            self._options_data.update(user_input)
            preview_name = (user_input.get(CONF_NAME) or "").strip()
            if not preview_name:
                preview_name = self._options_data.get(CONF_NAME) or self.config_entry.title
            self._options_data[CONF_NAME] = preview_name

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=preview_name,
                data={**self.config_entry.data, **self._options_data},
            )
            return self.async_create_entry(title="", data=self._options_data)

        calc = SolarCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            elevation=self.hass.config.elevation,
            tz=dt_util.DEFAULT_TIME_ZONE,
        )
        preview_text = calc.get_seasonal_preview_text(
            target_hours=self._options_data[CONF_TARGET_PHOTOPERIOD],
            mode=self._options_data[CONF_LIGHTING_MODE],
            morning_split_pct=self._options_data[CONF_MORNING_SPLIT],
            overlap_hours=self._options_data[CONF_DAYLIGHT_OVERLAP],
            earliest_start=self._options_data.get(CONF_EARLIEST_START, DEFAULT_EARLIEST_START),
            latest_end=self._options_data.get(CONF_LATEST_END, DEFAULT_LATEST_END),
        )

        current_name = self._options_data.get(CONF_NAME, self.config_entry.title)
        preview_schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=current_name,
                ): selector.TextSelector(),
                vol.Required(
                    CONF_TARGET_PHOTOPERIOD,
                    default=float(self._options_data.get(CONF_TARGET_PHOTOPERIOD, DEFAULT_TARGET_PHOTOPERIOD)),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_PHOTOPERIOD,
                        max=MAX_PHOTOPERIOD,
                        step=STEP_PHOTOPERIOD,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_EARLIEST_START,
                    default=str(self._options_data.get(CONF_EARLIEST_START, DEFAULT_EARLIEST_START)),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_LATEST_END,
                    default=str(self._options_data.get(CONF_LATEST_END, DEFAULT_LATEST_END)),
                ): selector.TimeSelector(),
            }
        )

        return self.async_show_form(
            step_id="preview",
            data_schema=preview_schema,
            description_placeholders={
                "preview_text": preview_text,
                "target_hours": str(self._options_data[CONF_TARGET_PHOTOPERIOD]),
            },
        )


