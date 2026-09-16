"""Coordinator and runtime scheduler for Adaptive Growth Light."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
import zoneinfo

from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.event import async_track_point_in_time, async_track_time_interval
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
    DEFAULT_ENABLED,
    DEFAULT_LATEST_END,
    DEFAULT_LIGHTING_MODE,
    DEFAULT_MORNING_SPLIT,
    DEFAULT_NAME,
    DEFAULT_TARGET_PHOTOPERIOD,
    DOMAIN,
)
from .solar import DailyPhotoperiod, NextSession, SolarCalculator, parse_time_helper

_LOGGER = logging.getLogger(__name__)


class AdaptiveGrowthLightCoordinator:
    """Manages solar photoperiod calculations and automated lighting schedules."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        data: dict[str, Any],
        sw_version: str = "1.1.6",
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.name: str = data.get(CONF_NAME, DEFAULT_NAME)
        self.target_entity: str = data.get(CONF_TARGET_ENTITY, "")
        self.target_photoperiod: float = float(
            data.get(CONF_TARGET_PHOTOPERIOD, DEFAULT_TARGET_PHOTOPERIOD)
        )
        self.lighting_mode: str = data.get(CONF_LIGHTING_MODE, DEFAULT_LIGHTING_MODE)
        self.morning_split: float = float(
            data.get(CONF_MORNING_SPLIT, DEFAULT_MORNING_SPLIT)
        )
        self.daylight_overlap: float = float(
            data.get(CONF_DAYLIGHT_OVERLAP, DEFAULT_DAYLIGHT_OVERLAP)
        )
        self.earliest_start = parse_time_helper(data.get(CONF_EARLIEST_START))
        self.latest_end = parse_time_helper(data.get(CONF_LATEST_END))
        self.is_enabled: bool = DEFAULT_ENABLED
        self.sw_version: str = sw_version

        # Track if light was turned on by this automation
        self._turned_on_by_automation: bool = False

        # Timer cancellation callbacks
        self._unsub_timers: list[CALLBACK_TYPE] = []
        self._unsub_interval: CALLBACK_TYPE | None = None
        self._listeners: list[Callable[[], None]] = []

        # Initialize solar calculator with Home Assistant's coordinates
        tz = dt_util.DEFAULT_TIME_ZONE
        self.solar_calculator = SolarCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            elevation=self.hass.config.elevation,
            tz=tz,
        )

        self.today_plan: DailyPhotoperiod | None = None
        self.next_session: NextSession | None = None
        self.status: str = "initial"

    async def async_setup(self) -> None:
        """Start scheduler and calculate initial plan."""
        self.recalculate()

        # Re-evaluate schedule every 15 minutes to keep next-session and status up to date
        self._unsub_interval = async_track_time_interval(
            self.hass, self._async_interval_tick, timedelta(minutes=15)
        )

        # Apply initial state
        await self._async_evaluate_and_schedule()

    def add_listener(self, update_callback: Callable[[], None]) -> CALLBACK_TYPE:
        """Register a callback for coordinator updates."""
        self._listeners.append(update_callback)

        def remove_listener() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return remove_listener

    def _notify_listeners(self) -> None:
        """Notify all registered listeners."""
        for callback in self._listeners:
            try:
                callback()
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.error("Error notifying listener in %s: %s", self.name, ex)

    def recalculate(self) -> None:
        """Recalculate daily photoperiod and next session based on current time."""
        now = dt_util.now()
        self.today_plan = self.solar_calculator.get_daily_photoperiod(
            calc_date=now.date(),
            target_hours=self.target_photoperiod,
            mode=self.lighting_mode,
            morning_split_pct=self.morning_split,
            overlap_hours=self.daylight_overlap,
            earliest_start=self.earliest_start,
            latest_end=self.latest_end,
        )
        self.next_session = self.solar_calculator.get_next_session(
            now=now,
            target_hours=self.target_photoperiod,
            mode=self.lighting_mode,
            morning_split_pct=self.morning_split,
            overlap_hours=self.daylight_overlap,
            earliest_start=self.earliest_start,
            latest_end=self.latest_end,
        )
        self.status = self.solar_calculator.get_current_status(
            now=now,
            target_hours=self.target_photoperiod,
            mode=self.lighting_mode,
            morning_split_pct=self.morning_split,
            overlap_hours=self.daylight_overlap,
            earliest_start=self.earliest_start,
            latest_end=self.latest_end,
            is_enabled=self.is_enabled,
        )

    async def _async_interval_tick(self, _now: datetime) -> None:
        """Periodic tick to update status, next session, and verify schedule."""
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    def _cancel_scheduled_timers(self) -> None:
        """Cancel all pending point-in-time timers."""
        for unsub in self._unsub_timers:
            unsub()
        self._unsub_timers.clear()

    async def _async_evaluate_and_schedule(self) -> None:
        """Evaluate if the light should be ON or OFF right now and schedule future events."""
        self._cancel_scheduled_timers()

        if not self.is_enabled:
            # If disabled and we turned it on, turn it off
            if self._turned_on_by_automation:
                await self._async_turn_light(False)
            self._notify_listeners()
            return

        now = dt_util.now()
        plan = self.today_plan
        if not plan:
            return

        # Check if currently inside morning or evening window
        in_morning = plan.morning_session is not None and plan.morning_session.is_active(now)
        in_evening = plan.evening_session is not None and plan.evening_session.is_active(now)
        should_be_on = in_morning or in_evening

        if should_be_on:
            if not self._is_light_on():
                await self._async_turn_light(True)
        else:
            if self._turned_on_by_automation and self._is_light_on():
                await self._async_turn_light(False)

        # Schedule upcoming events for today
        events_to_schedule: list[tuple[datetime, bool]] = []

        if plan.morning_session:
            if plan.morning_session.start > now:
                events_to_schedule.append((plan.morning_session.start, True))
            if plan.morning_session.end > now:
                events_to_schedule.append((plan.morning_session.end, False))

        if plan.evening_session:
            if plan.evening_session.start > now:
                events_to_schedule.append((plan.evening_session.start, True))
            if plan.evening_session.end > now:
                events_to_schedule.append((plan.evening_session.end, False))

        # Schedule midnight recalculation for the next day
        tomorrow_midnight = datetime.combine(
            now.date() + timedelta(days=1), datetime.min.time(), tzinfo=now.tzinfo
        )
        if tomorrow_midnight > now:
            events_to_schedule.append((tomorrow_midnight, None))

        for event_time, action in events_to_schedule:
            self._schedule_event(event_time, action)

    def _schedule_event(self, event_time: datetime, turn_on: bool | None) -> None:
        """Schedule an action at a specific point in time."""
        async def _callback(_now: datetime) -> None:
            if turn_on is not None:
                if self.is_enabled:
                    await self._async_turn_light(turn_on)
            self.recalculate()
            await self._async_evaluate_and_schedule()
            self._notify_listeners()

        unsub = async_track_point_in_time(self.hass, _callback, event_time)
        self._unsub_timers.append(unsub)

    def _is_light_on(self) -> bool:
        """Check if target light/switch entity is currently turned ON."""
        if not self.target_entity:
            return False
        state = self.hass.states.get(self.target_entity)
        return state is not None and state.state == "on"

    async def _async_turn_light(self, turn_on: bool) -> None:
        """Turn on or off the target switch or light entity."""
        if not self.target_entity:
            return

        service = "turn_on" if turn_on else "turn_off"
        domain = self.target_entity.split(".")[0]
        if domain not in ("light", "switch"):
            domain = "homeassistant"

        _LOGGER.info(
            "Adaptive Growth Light '%s': turning %s target entity %s",
            self.name,
            service,
            self.target_entity,
        )

        try:
            await self.hass.services.async_call(
                domain,
                service,
                {"entity_id": self.target_entity},
                blocking=False,
            )
            self._turned_on_by_automation = turn_on
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Failed to execute %s on %s: %s", service, self.target_entity, ex)

    # ----------------- Dynamic Entity Setters -----------------

    async def async_set_enabled(self, enabled: bool) -> None:
        """Toggle master automation switch."""
        self.is_enabled = enabled
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    async def async_set_target_photoperiod(self, hours: float) -> None:
        """Update target photoperiod hours."""
        self.target_photoperiod = hours
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    async def async_set_lighting_mode(self, mode: str) -> None:
        """Update lighting mode (morning, evening, both)."""
        self.lighting_mode = mode
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    async def async_set_morning_split(self, split: float) -> None:
        """Update morning/evening split percentage."""
        self.morning_split = split
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    async def async_set_daylight_overlap(self, overlap: float) -> None:
        """Update daylight overlap hours."""
        self.daylight_overlap = overlap
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    async def async_set_earliest_start(self, earliest: Any) -> None:
        """Update earliest morning turn-on cut-off."""
        self.earliest_start = parse_time_helper(earliest)
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    async def async_set_latest_end(self, latest: Any) -> None:
        """Update latest evening turn-off cut-off."""
        self.latest_end = parse_time_helper(latest)
        self.recalculate()
        await self._async_evaluate_and_schedule()
        self._notify_listeners()

    def get_seasonal_matrix(self) -> list[dict[str, Any]]:
        """Return 12-month solar and supplementary light breakdown."""
        return self.solar_calculator.get_seasonal_matrix(
            target_hours=self.target_photoperiod,
            mode=self.lighting_mode,
            morning_split_pct=self.morning_split,
            overlap_hours=self.daylight_overlap,
            earliest_start=self.earliest_start,
            latest_end=self.latest_end,
        )

    def get_annual_earliest_turn_on(self) -> dict[str, Any]:
        """Return annual earliest turn-on statistics."""
        now = dt_util.now()
        return self.solar_calculator.get_annual_earliest_turn_on(
            year=now.year,
            target_hours=self.target_photoperiod,
            mode=self.lighting_mode,
            morning_split_pct=self.morning_split,
            overlap_hours=self.daylight_overlap,
            earliest_start=self.earliest_start,
            latest_end=self.latest_end,
        )

    def async_unload(self) -> None:
        """Clean up timers and subscriptions upon unload."""
        self._cancel_scheduled_timers()
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None
        self._listeners.clear()
