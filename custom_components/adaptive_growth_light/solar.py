"""Solar photoperiod calculations for Adaptive Growth Light."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from typing import Any
import zoneinfo

from astral import Observer
from astral.sun import sun


@dataclass(frozen=True)
class SessionWindow:
    """Represents a scheduled supplementary lighting session window."""

    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        """Duration of the session window."""
        return self.end - self.start

    @property
    def duration_hours(self) -> float:
        """Duration in fractional hours."""
        return round(self.duration.total_seconds() / 3600.0, 2)

    def is_active(self, now: datetime) -> bool:
        """Return True if the given datetime falls within this session window."""
        return self.start <= now < self.end


@dataclass(frozen=True)
class DailyPhotoperiod:
    """Calculated daily photoperiod and supplementary lighting plan."""

    calc_date: date
    sunrise: datetime | None
    sunset: datetime | None
    natural_daylight: timedelta
    target_photoperiod: timedelta
    supplementary_duration: timedelta
    morning_session: SessionWindow | None
    evening_session: SessionWindow | None
    overlap: timedelta

    @property
    def natural_daylight_hours(self) -> float:
        """Natural daylight in fractional hours."""
        return round(self.natural_daylight.total_seconds() / 3600.0, 2)

    @property
    def target_hours(self) -> float:
        """Target photoperiod in fractional hours."""
        return round(self.target_photoperiod.total_seconds() / 3600.0, 2)

    @property
    def supplementary_hours(self) -> float:
        """Required supplementary duration in fractional hours."""
        return round(self.supplementary_duration.total_seconds() / 3600.0, 2)


@dataclass(frozen=True)
class NextSession:
    """Information about the upcoming supplementary lighting session."""

    session_type: str  # "morning" | "evening" | "none"
    start: datetime | None
    end: datetime | None
    duration: timedelta
    seconds_until: float


class SolarCalculator:
    """Calculates photoperiod and supplementary lighting schedules using astral."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        elevation: float = 0.0,
        tz: tzinfo | None = None,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.tz = tz or zoneinfo.ZoneInfo("UTC")
        self.observer = Observer(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
        )

    def get_daily_photoperiod(
        self,
        calc_date: date,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
    ) -> DailyPhotoperiod:
        """Calculate the daily photoperiod and schedule for a specific date."""
        target_td = timedelta(hours=max(0.0, target_hours))
        overlap_td = timedelta(hours=max(0.0, overlap_hours))

        try:
            sun_data = sun(self.observer, date=calc_date, tzinfo=self.tz)
            sunrise: datetime | None = sun_data.get("sunrise")
            sunset: datetime | None = sun_data.get("sunset")
        except ValueError:
            # Handle polar day or polar night where sun doesn't rise or set
            sunrise = None
            sunset = None

        # Calculate natural daylight duration
        if sunrise and sunset:
            natural_daylight = max(timedelta(0), sunset - sunrise)
        else:
            # Fallback estimation for polar edge conditions
            # If summer in northern hemisphere and latitude > 66.5, ~24h daylight
            is_summer = 3 <= calc_date.month <= 9
            is_north = self.latitude >= 0
            if (is_summer and is_north) or (not is_summer and not is_north):
                natural_daylight = timedelta(hours=24)
            else:
                natural_daylight = timedelta(0)

        # Supplementary lighting needed
        if natural_daylight >= target_td:
            supplementary_td = timedelta(0)
        else:
            supplementary_td = target_td - natural_daylight

        supp_seconds = supplementary_td.total_seconds()

        # Split into morning and evening components
        mode_clean = mode.lower().strip()
        if supp_seconds <= 0:
            morn_seconds = 0.0
            eve_seconds = 0.0
        elif mode_clean == "morning":
            morn_seconds = supp_seconds
            eve_seconds = 0.0
        elif mode_clean == "evening":
            morn_seconds = 0.0
            eve_seconds = supp_seconds
        else:  # "both"
            ratio = max(0.0, min(100.0, morning_split_pct)) / 100.0
            morn_seconds = supp_seconds * ratio
            eve_seconds = supp_seconds - morn_seconds

        morning_session: SessionWindow | None = None
        evening_session: SessionWindow | None = None

        if sunrise and morn_seconds > 0:
            # Morning routine: ends at sunrise + overlap
            m_end = sunrise + overlap_td
            m_start = m_end - timedelta(seconds=morn_seconds)
            morning_session = SessionWindow(start=m_start, end=m_end)

        if sunset and eve_seconds > 0:
            # Evening routine: starts at sunset - overlap
            e_start = sunset - overlap_td
            e_end = e_start + timedelta(seconds=eve_seconds)
            evening_session = SessionWindow(start=e_start, end=e_end)

        return DailyPhotoperiod(
            calc_date=calc_date,
            sunrise=sunrise,
            sunset=sunset,
            natural_daylight=natural_daylight,
            target_photoperiod=target_td,
            supplementary_duration=supplementary_td,
            morning_session=morning_session,
            evening_session=evening_session,
            overlap=overlap_td,
        )

    def get_current_status(
        self,
        now: datetime,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        is_enabled: bool = True,
    ) -> str:
        """Determine the current status string based on the active plan and time."""
        if not is_enabled:
            return "disabled"

        today_plan = self.get_daily_photoperiod(
            now.date(), target_hours, mode, morning_split_pct, overlap_hours
        )

        if today_plan.morning_session and today_plan.morning_session.is_active(now):
            return "supplementing_morning"

        if today_plan.evening_session and today_plan.evening_session.is_active(now):
            return "supplementing_evening"

        if today_plan.sunrise and today_plan.sunset:
            if today_plan.sunrise <= now < today_plan.sunset:
                return "daylight_active"

        return "night_idle"

    def get_next_session(
        self,
        now: datetime,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
    ) -> NextSession:
        """Find the next upcoming supplementary session (today or in future days)."""
        # Search up to 3 days ahead
        for day_offset in range(3):
            check_date = now.date() + timedelta(days=day_offset)
            plan = self.get_daily_photoperiod(
                check_date, target_hours, mode, morning_split_pct, overlap_hours
            )

            # Check morning session
            if plan.morning_session and plan.morning_session.end > now:
                # If it's already active or in the future
                start = plan.morning_session.start
                end = plan.morning_session.end
                seconds = max(0.0, (start - now).total_seconds())
                return NextSession(
                    session_type="morning",
                    start=start,
                    end=end,
                    duration=plan.morning_session.duration,
                    seconds_until=seconds,
                )

            # Check evening session
            if plan.evening_session and plan.evening_session.end > now:
                start = plan.evening_session.start
                end = plan.evening_session.end
                seconds = max(0.0, (start - now).total_seconds())
                return NextSession(
                    session_type="evening",
                    start=start,
                    end=end,
                    duration=plan.evening_session.duration,
                    seconds_until=seconds,
                )

        return NextSession(
            session_type="none",
            start=None,
            end=None,
            duration=timedelta(0),
            seconds_until=0.0,
        )

    def get_seasonal_matrix(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a 12-month breakdown (on the 15th of each month) of solar and supplementary light."""
        if year is None:
            year = datetime.now(self.tz).year

        months_data = []
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        for m_idx in range(1, 13):
            sample_date = date(year, m_idx, 15)
            plan = self.get_daily_photoperiod(
                sample_date,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
            )

            months_data.append({
                "month": m_idx,
                "name": month_names[m_idx - 1],
                "natural_hours": plan.natural_daylight_hours,
                "supplementary_hours": plan.supplementary_hours,
                "target_hours": plan.target_hours,
                "sunrise": plan.sunrise.strftime("%H:%M") if plan.sunrise else None,
                "sunset": plan.sunset.strftime("%H:%M") if plan.sunset else None,
                "morning_hours": plan.morning_session.duration_hours if plan.morning_session else 0.0,
                "evening_hours": plan.evening_session.duration_hours if plan.evening_session else 0.0,
            })

        return months_data

    def get_seasonal_preview_text(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        ref_year: int | None = None,
    ) -> str:
        """Format a clear seasonal breakdown text for config flow preview dialog."""
        year = ref_year or datetime.now(self.tz).year
        today = datetime.now(self.tz).date()

        dates = [
            ("☀️ Summer Solstice (Jun 21)", date(year, 6, 21)),
            ("🍂 Autumn Midpoint (Oct 15)", date(year, 10, 15)),
            ("❄️ Winter Solstice (Dec 21)", date(year, 12, 21)),
            ("🌱 Spring Midpoint (Apr 15)", date(year, 4, 15)),
        ]

        lines = [
            f"Target: **{target_hours}h** photoperiod ({mode.capitalize()} mode, {overlap_hours}h daylight overlap)\n"
        ]

        for label, d in dates:
            plan = self.get_daily_photoperiod(
                d, target_hours, mode, morning_split_pct, overlap_hours
            )
            nat = plan.natural_daylight_hours
            supp = plan.supplementary_hours
            if supp <= 0:
                action = "🌱 Light stays OFF (natural sunlight sufficient)"
            elif mode == "morning":
                action = f"💡 Runs {supp}h before sunrise"
            elif mode == "evening":
                action = f"💡 Runs {supp}h after sunset"
            else:
                m_h = plan.morning_session.duration_hours if plan.morning_session else 0.0
                e_h = plan.evening_session.duration_hours if plan.evening_session else 0.0
                action = f"💡 {m_h}h morning + {e_h}h evening"

            lines.append(f"- **{label}**: {nat}h daylight ➔ **{supp}h** supplement\n  _{action}_")

        today_plan = self.get_daily_photoperiod(
            today, target_hours, mode, morning_split_pct, overlap_hours
        )
        lines.append(
            f"\n🗓️ **Today ({today.strftime('%b %d')})**: {today_plan.natural_daylight_hours}h natural daylight ➔ **{today_plan.supplementary_hours}h** supplement today."
        )

        return "\n".join(lines)

