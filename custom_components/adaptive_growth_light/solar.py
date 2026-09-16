"""Solar photoperiod calculations for Adaptive Growth Light."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
from typing import Any
import zoneinfo

from astral import Observer
from astral.sun import sun


def parse_time_helper(val: time | str | None) -> time | None:
    """Safely parse a time object or string into a datetime.time object."""
    if val is None or isinstance(val, time):
        return val
    if isinstance(val, str) and val.strip():
        parts = val.strip().split(":")
        try:
            return time(
                int(parts[0]),
                int(parts[1]),
                int(parts[2]) if len(parts) > 2 else 0,
            )
        except (ValueError, IndexError):
            return None
    return None


@dataclass(frozen=True)
class SessionWindow:
    """Represents a scheduled supplementary lighting session window."""

    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        """Duration of the session window."""
        return max(timedelta(0), self.end - self.start)

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
    earliest_start: time | None = None
    latest_end: time | None = None
    unclamped_morning_session: SessionWindow | None = None
    unclamped_evening_session: SessionWindow | None = None
    morning_displaced_duration: timedelta = timedelta(0)
    evening_displaced_duration: timedelta = timedelta(0)

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

    @property
    def actual_supplementary_duration(self) -> timedelta:
        """Actual supplementary lighting duration after cut-off clamping."""
        m_sec = self.morning_session.duration.total_seconds() if self.morning_session else 0.0
        e_sec = self.evening_session.duration.total_seconds() if self.evening_session else 0.0
        return timedelta(seconds=m_sec + e_sec)

    @property
    def actual_supplementary_hours(self) -> float:
        """Actual supplementary lighting duration in fractional hours."""
        return round(self.actual_supplementary_duration.total_seconds() / 3600.0, 2)

    @property
    def actual_photoperiod(self) -> timedelta:
        """Total actual light received (natural + actual supplementary)."""
        return self.natural_daylight + self.actual_supplementary_duration

    @property
    def actual_photoperiod_hours(self) -> float:
        """Total actual light received in fractional hours."""
        return round(self.actual_photoperiod.total_seconds() / 3600.0, 2)


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
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
    ) -> DailyPhotoperiod:
        """Calculate the daily photoperiod and schedule for a specific date, enforcing sleep cut-offs."""
        target_td = timedelta(hours=max(0.0, target_hours))
        overlap_td = timedelta(hours=max(0.0, overlap_hours))

        parsed_earliest = parse_time_helper(earliest_start)
        parsed_latest = parse_time_helper(latest_end)

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

        unclamped_morning: SessionWindow | None = None
        morning_session: SessionWindow | None = None
        morn_displaced_td = timedelta(0)

        if sunrise and morn_seconds > 0:
            # Morning routine: ends at sunrise + overlap
            # If overlap exceeds session duration, scale it to half the duration so it always starts in pre-sunrise darkness
            morn_td = timedelta(seconds=morn_seconds)
            eff_overlap_morn = (
                timedelta(seconds=morn_seconds / 2.0)
                if overlap_td >= morn_td
                else overlap_td
            )
            m_end = sunrise + eff_overlap_morn
            m_start = m_end - morn_td
            unclamped_morning = SessionWindow(start=m_start, end=m_end)

            # Apply morning cut-off if configured
            if parsed_earliest:
                cutoff_dt = datetime.combine(m_start.date(), parsed_earliest, tzinfo=m_start.tzinfo)
                if m_start < cutoff_dt:
                    if cutoff_dt < m_end:
                        morning_session = SessionWindow(start=cutoff_dt, end=m_end)
                        actual_morn_sec = (m_end - cutoff_dt).total_seconds()
                    else:
                        morning_session = None
                        actual_morn_sec = 0.0
                    morn_displaced_sec = max(0.0, morn_seconds - actual_morn_sec)
                    morn_displaced_td = timedelta(seconds=morn_displaced_sec)
                else:
                    morning_session = unclamped_morning
            else:
                morning_session = unclamped_morning

        # Reallocate any light cut off in morning to the evening session!
        if morn_displaced_td.total_seconds() > 0 and mode_clean in ("both", "morning"):
            eve_seconds += morn_displaced_td.total_seconds()

        unclamped_evening: SessionWindow | None = None
        evening_session: SessionWindow | None = None
        eve_displaced_td = timedelta(0)

        if sunset and eve_seconds > 0:
            # Evening routine: starts at sunset - overlap
            # If overlap exceeds session duration, scale it to half the duration so it always extends into post-sunset darkness
            eve_td = timedelta(seconds=eve_seconds)
            eff_overlap_eve = (
                timedelta(seconds=eve_seconds / 2.0)
                if overlap_td >= eve_td
                else overlap_td
            )
            e_start = sunset - eff_overlap_eve
            e_end = e_start + eve_td
            unclamped_evening = SessionWindow(start=e_start, end=e_end)

            # Apply evening cut-off if configured
            if parsed_latest:
                cutoff_dt = datetime.combine(e_end.date(), parsed_latest, tzinfo=e_end.tzinfo)
                if e_end > cutoff_dt:
                    if cutoff_dt > e_start:
                        evening_session = SessionWindow(start=e_start, end=cutoff_dt)
                        actual_eve_sec = (cutoff_dt - e_start).total_seconds()
                    else:
                        evening_session = None
                        actual_eve_sec = 0.0
                    eve_displaced_sec = max(0.0, eve_seconds - actual_eve_sec)
                    eve_displaced_td = timedelta(seconds=eve_displaced_sec)
                else:
                    evening_session = unclamped_evening
            else:
                evening_session = unclamped_evening

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
            earliest_start=parsed_earliest,
            latest_end=parsed_latest,
            unclamped_morning_session=unclamped_morning,
            unclamped_evening_session=unclamped_evening,
            morning_displaced_duration=morn_displaced_td,
            evening_displaced_duration=eve_displaced_td,
        )

    def get_annual_earliest_turn_on(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """Calculate the earliest astronomical and effective turn-on hour across the entire year."""
        if year is None:
            year = datetime.now(self.tz).year

        earliest_astronomical_dt: datetime | None = None
        earliest_astronomical_date: date | None = None
        earliest_effective_dt: datetime | None = None
        is_clamped = False

        parsed_earliest = parse_time_helper(earliest_start)

        start_date = date(year, 1, 1)
        for day_idx in range(365):
            current_date = start_date + timedelta(days=day_idx)
            plan = self.get_daily_photoperiod(
                current_date,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
                earliest_start=earliest_start,
                latest_end=latest_end,
            )

            unclamped_m = plan.unclamped_morning_session
            if unclamped_m:
                t = unclamped_m.start.time()
                if (
                    earliest_astronomical_dt is None
                    or t < earliest_astronomical_dt.time()
                ):
                    earliest_astronomical_dt = unclamped_m.start
                    earliest_astronomical_date = current_date

            if plan.morning_session:
                t_eff = plan.morning_session.start.time()
                if earliest_effective_dt is None or t_eff < earliest_effective_dt.time():
                    earliest_effective_dt = plan.morning_session.start

        unclamped_str = (
            earliest_astronomical_dt.strftime("%H:%M")
            if earliest_astronomical_dt
            else "--:--"
        )
        effective_str = (
            earliest_effective_dt.strftime("%H:%M") if earliest_effective_dt else "--:--"
        )
        if (
            parsed_earliest
            and earliest_astronomical_dt
            and earliest_astronomical_dt.time() < parsed_earliest
        ):
            is_clamped = True

        return {
            "unclamped_time": unclamped_str,
            "effective_time": effective_str,
            "date": earliest_astronomical_date,
            "is_clamped": is_clamped,
            "cutoff_time": parsed_earliest.strftime("%H:%M") if parsed_earliest else None,
        }

    def get_precision_ascii_timeline(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
        year: int | None = None,
    ) -> str:
        """Render a strict 48-slot fixed-width timeline ruler for terminal and text fallback."""
        if year is None:
            year = datetime.now(self.tz).year

        benchmarks = [
            ("Winter Solstice", date(year, 12, 21)),
            ("Spring Equinox", date(year, 3, 20)),
            ("Summer Solstice", date(year, 6, 21)),
            ("Autumn Equinox", date(year, 9, 22)),
        ]

        header = "                00:00 03:00 06:00 09:00 12:00 15:00 18:00 21:00 24:00"
        ruler = "                ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤"

        lines = [header, ruler]

        parsed_cs = parse_time_helper(earliest_start)
        parsed_ce = parse_time_helper(latest_end)
        cs_h = (parsed_cs.hour + parsed_cs.minute / 60.0) if parsed_cs else None
        ce_h = (parsed_ce.hour + parsed_ce.minute / 60.0) if parsed_ce else None

        for name, d in benchmarks:
            plan = self.get_daily_photoperiod(
                d,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
                earliest_start=earliest_start,
                latest_end=latest_end,
            )

            sr_h = (plan.sunrise.hour + plan.sunrise.minute / 60.0) if plan.sunrise else None
            ss_h = (plan.sunset.hour + plan.sunset.minute / 60.0) if plan.sunset else None

            uncl_ms_h = None
            if plan.unclamped_morning_session:
                st = plan.unclamped_morning_session.start
                uncl_ms_h = st.hour + st.minute / 60.0

            ms_h = (plan.morning_session.start.hour + plan.morning_session.start.minute / 60.0) if plan.morning_session else None
            me_h = (plan.morning_session.end.hour + plan.morning_session.end.minute / 60.0) if plan.morning_session else None
            es_h = (plan.evening_session.start.hour + plan.evening_session.start.minute / 60.0) if plan.evening_session else None
            ee_h = (plan.evening_session.end.hour + plan.evening_session.end.minute / 60.0) if plan.evening_session else None

            row_cells = []
            for slot in range(48):
                mid = (slot + 0.5) * 0.5
                is_day = sr_h is not None and ss_h is not None and sr_h <= mid < ss_h
                is_morn_active = ms_h is not None and me_h is not None and ms_h <= mid < me_h
                is_eve_active = es_h is not None and ee_h is not None and es_h <= mid < ee_h

                is_morn_suppressed = False
                if uncl_ms_h is not None and cs_h is not None:
                    m_end = plan.unclamped_morning_session.end
                    uncl_me_h = m_end.hour + m_end.minute / 60.0
                    if uncl_ms_h <= mid < min(cs_h, uncl_me_h):
                        is_morn_suppressed = True

                is_eve_suppressed = False
                if plan.unclamped_evening_session and ce_h is not None:
                    uncl_ee_h = plan.unclamped_evening_session.end.hour + plan.unclamped_evening_session.end.minute / 60.0
                    if ce_h <= mid < uncl_ee_h:
                        is_eve_suppressed = True

                if is_day:
                    row_cells.append("█")
                elif is_morn_active or is_eve_active:
                    row_cells.append("░")
                elif is_morn_suppressed or is_eve_suppressed:
                    row_cells.append("x")
                else:
                    row_cells.append("·")

            row_str = "".join(row_cells)
            lines.append(f"{name:<15} │{row_str}│")

        lines.append(ruler)
        lines.append("Legend:  █ Natural Sunlight    ░ Artificial Light    x Suppressed by Cut-Off    · Night (Off)")
        return "\n".join(lines)

    def generate_svg_timeline_b64(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
        year: int | None = None,
    ) -> str:
        """Generate a rich, responsive vector SVG seasonal timeline with embedded benchmark statistics."""
        if year is None:
            year = datetime.now(self.tz).year

        benchmarks = [
            ("Winter Solstice", date(year, 12, 21), "Dec 21"),
            ("Spring Equinox", date(year, 3, 20), "Mar 20"),
            ("Summer Solstice", date(year, 6, 21), "Jun 21"),
            ("Autumn Equinox", date(year, 9, 22), "Sep 22"),
        ]

        def fmt_dur(td: timedelta) -> str:
            secs = max(0, int(td.total_seconds()))
            h = secs // 3600
            m = (secs % 3600) // 60
            return f"{h}h {m:02d}m"

        def fmt_time_span(s: SessionWindow | None) -> str:
            if not s:
                return "Off"
            st = s.start.strftime("%H:%M")
            en = s.end.strftime("%H:%M")
            return f"{st} – {en} ({fmt_dur(s.duration)})"

        W = 860
        H = 360
        left = 40
        right = 820
        t_width = right - left

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" height="auto" style="background:#0f172a;border-radius:12px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">',
            '<defs>',
            '  <pattern id="cutHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">',
            '    <line x1="0" y1="0" x2="0" y2="8" stroke="#ef4444" stroke-width="2.5" opacity="0.85" />',
            '  </pattern>',
            '</defs>',
        ]

        # Top 24h Ruler and vertical grid lines
        for h in range(0, 25, 3):
            x = left + (h / 24.0) * t_width
            svg.append(f'<line x1="{x:.1f}" y1="26" x2="{x:.1f}" y2="{H-40}" stroke="#1e293b" stroke-width="1" stroke-dasharray="3,3" />')
            anchor = "start" if h == 0 else ("end" if h == 24 else "middle")
            svg.append(f'<text x="{x:.1f}" y="19" fill="#94a3b8" font-size="11" font-weight="500" text-anchor="{anchor}">{h:02d}:00</text>')

        parsed_cs = parse_time_helper(earliest_start)
        parsed_ce = parse_time_helper(latest_end)
        cs_h = (parsed_cs.hour + parsed_cs.minute / 60.0) if parsed_cs else None
        ce_h = (parsed_ce.hour + parsed_ce.minute / 60.0) if parsed_ce else None

        if cs_h is not None:
            cx = left + (cs_h / 24.0) * t_width
            svg.append(f'<line x1="{cx:.1f}" y1="26" x2="{cx:.1f}" y2="{H-40}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.8" />')
        if ce_h is not None:
            cx = left + (ce_h / 24.0) * t_width
            svg.append(f'<line x1="{cx:.1f}" y1="26" x2="{cx:.1f}" y2="{H-40}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.8" />')

        start_y = 36
        block_h = 70
        bar_h = 16

        for idx, (label, d, date_str) in enumerate(benchmarks):
            y_base = start_y + idx * block_h
            y_title = y_base + 14
            y_bar = y_base + 22
            y_sub = y_base + 51

            plan = self.get_daily_photoperiod(
                d,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
                earliest_start=earliest_start,
                latest_end=latest_end,
            )

            # Benchmark stats calculation
            if plan.sunrise and plan.sunset:
                sun_dur_str = fmt_dur(plan.sunset - plan.sunrise)
                sun_txt = f"{plan.sunrise.strftime('%H:%M')} – {plan.sunset.strftime('%H:%M')}"
            else:
                sun_dur_str = f"{plan.natural_daylight_hours:.1f}h"
                sun_txt = "Polar Day / Night"

            morn_dur_td = plan.morning_session.duration if plan.morning_session else timedelta(0)
            eve_dur_td = plan.evening_session.duration if plan.evening_session else timedelta(0)
            tot_grow_td = morn_dur_td + eve_dur_td

            grow_dur_str = fmt_dur(tot_grow_td) if tot_grow_td.total_seconds() > 0 else "Off"
            tot_hrs_str = f"{plan.actual_photoperiod_hours:.1f}h"

            morn_txt = fmt_time_span(plan.morning_session)
            if not plan.morning_session:
                if plan.unclamped_morning_session:
                    morn_txt = "Off (Held back by cut-off)"
                elif plan.supplementary_hours <= 0:
                    morn_txt = "Off (Sunlight exceeds target)"
                else:
                    morn_txt = "Off"

            eve_txt = fmt_time_span(plan.evening_session)
            if not plan.evening_session:
                if plan.unclamped_evening_session:
                    eve_txt = "Off (Held back by cut-off)"
                elif plan.supplementary_hours <= 0:
                    eve_txt = "Off (Sunlight exceeds target)"
                else:
                    eve_txt = "Off"

            # Top Line: Benchmark Name & High-level Statistics
            svg.append(f'<text x="{left}" y="{y_title}" fill="#f8fafc" font-size="13" font-weight="700">{label} <tspan fill="#94a3b8" font-size="11" font-weight="400">({date_str})</tspan></text>')
            svg.append(f'<text x="{right}" y="{y_title}" text-anchor="end" font-size="11" fill="#94a3b8">Daylight: <tspan fill="#f59e0b" font-weight="600">{sun_dur_str}</tspan>  •  Grow Light: <tspan fill="#10b981" font-weight="600">{grow_dur_str}</tspan>  •  Total: <tspan fill="#38bdf8" font-weight="700">{tot_hrs_str}</tspan></text>')

            # Background Timeline Bar
            svg.append(f'<rect x="{left}" y="{y_bar}" width="{t_width}" height="{bar_h}" rx="4" fill="#1e293b" />')

            # Natural Sunlight segment
            if plan.sunrise and plan.sunset:
                sr_h = plan.sunrise.hour + plan.sunrise.minute / 60.0
                ss_h = plan.sunset.hour + plan.sunset.minute / 60.0
                x1 = left + (sr_h / 24.0) * t_width
                x2 = left + (ss_h / 24.0) * t_width
                svg.append(f'<rect x="{x1:.1f}" y="{y_bar}" width="{max(0.0, x2-x1):.1f}" height="{bar_h}" fill="#f59e0b" opacity="0.95" rx="2" />')

            # Morning Light & Cut-Off Suppressed segment
            if plan.unclamped_morning_session:
                u_st = plan.unclamped_morning_session.start.hour + plan.unclamped_morning_session.start.minute / 60.0
                u_en = plan.unclamped_morning_session.end.hour + plan.unclamped_morning_session.end.minute / 60.0
                if cs_h is not None and u_st < cs_h:
                    x1 = left + (u_st / 24.0) * t_width
                    x2 = left + (min(cs_h, u_en) / 24.0) * t_width
                    svg.append(f'<rect x="{x1:.1f}" y="{y_bar}" width="{max(0.0, x2-x1):.1f}" height="{bar_h}" fill="url(#cutHatch)" rx="2" />')
                if plan.morning_session:
                    m_st = plan.morning_session.start.hour + plan.morning_session.start.minute / 60.0
                    m_en = plan.morning_session.end.hour + plan.morning_session.end.minute / 60.0
                    x1 = left + (m_st / 24.0) * t_width
                    x2 = left + (m_en / 24.0) * t_width
                    svg.append(f'<rect x="{x1:.1f}" y="{y_bar}" width="{max(0.0, x2-x1):.1f}" height="{bar_h}" fill="#10b981" rx="2" />')
            elif plan.morning_session:
                m_st = plan.morning_session.start.hour + plan.morning_session.start.minute / 60.0
                m_en = plan.morning_session.end.hour + plan.morning_session.end.minute / 60.0
                x1 = left + (m_st / 24.0) * t_width
                x2 = left + (m_en / 24.0) * t_width
                svg.append(f'<rect x="{x1:.1f}" y="{y_bar}" width="{max(0.0, x2-x1):.1f}" height="{bar_h}" fill="#10b981" rx="2" />')

            # Evening Light segment
            if plan.evening_session:
                e_st = plan.evening_session.start.hour + plan.evening_session.start.minute / 60.0
                e_en = plan.evening_session.end.hour + plan.evening_session.end.minute / 60.0
                x1 = left + (e_st / 24.0) * t_width
                x2 = left + (e_en / 24.0) * t_width
                svg.append(f'<rect x="{x1:.1f}" y="{y_bar}" width="{max(0.0, x2-x1):.1f}" height="{bar_h}" fill="#10b981" rx="2" />')
            if plan.unclamped_evening_session and ce_h is not None:
                u_en = plan.unclamped_evening_session.end.hour + plan.unclamped_evening_session.end.minute / 60.0
                if u_en > ce_h:
                    x1 = left + (max(ce_h, plan.unclamped_evening_session.start.hour + plan.unclamped_evening_session.start.minute / 60.0) / 24.0) * t_width
                    x2 = left + (u_en / 24.0) * t_width
                    svg.append(f'<rect x="{x1:.1f}" y="{y_bar}" width="{max(0.0, x2-x1):.1f}" height="{bar_h}" fill="url(#cutHatch)" rx="2" />')

            # Bottom Line: Detailed Timing Sub-labels
            svg.append(f'<text x="{left}" y="{y_sub}" fill="#64748b" font-size="10.5">Morning: <tspan fill="#cbd5e1">{morn_txt}</tspan>    •    Sunlight: <tspan fill="#cbd5e1">{sun_txt}</tspan>    •    Evening: <tspan fill="#cbd5e1">{eve_txt}</tspan></text>')

        # Footer Legend
        leg_y = H - 16
        svg.append(f'<rect x="{left}" y="{leg_y - 9}" width="12" height="12" rx="2" fill="#f59e0b" />')
        svg.append(f'<text x="{left + 18}" y="{leg_y + 1}" fill="#cbd5e1" font-size="11">Natural Daylight</text>')

        svg.append(f'<rect x="{left + 150}" y="{leg_y - 9}" width="12" height="12" rx="2" fill="#10b981" />')
        svg.append(f'<text x="{left + 168}" y="{leg_y + 1}" fill="#cbd5e1" font-size="11">Active Grow Light</text>')

        svg.append(f'<rect x="{left + 310}" y="{leg_y - 9}" width="12" height="12" rx="2" fill="url(#cutHatch)" />')
        svg.append(f'<text x="{left + 328}" y="{leg_y + 1}" fill="#cbd5e1" font-size="11">Suppressed by Sleep Cut-Off</text>')

        svg.append('</svg>')
        svg_str = "".join(svg)
        b64 = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
        return f"![Seasonal Schedule Timeline](data:image/svg+xml;base64,{b64})"

    def get_exact_timing_markdown_table(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
        year: int | None = None,
    ) -> str:
        """Format an exact minute-level timing table comparing all seasonal benchmarks."""
        if year is None:
            year = datetime.now(self.tz).year

        benchmarks = [
            ("Winter Solstice (Dec 21)", date(year, 12, 21)),
            ("Spring Equinox (Mar 20)", date(year, 3, 20)),
            ("Summer Solstice (Jun 21)", date(year, 6, 21)),
            ("Autumn Equinox (Sep 22)", date(year, 9, 22)),
        ]

        rows = [
            "| Benchmark | Morning Grow Light | Natural Sunlight | Evening Grow Light | Total Light |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for label, d in benchmarks:
            plan = self.get_daily_photoperiod(
                d,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
                earliest_start=earliest_start,
                latest_end=latest_end,
            )

            # Natural Sunlight
            if plan.sunrise and plan.sunset:
                nat_dur = int(plan.natural_daylight.total_seconds() / 60)
                sun_str = f"{plan.sunrise.strftime('%H:%M')} – {plan.sunset.strftime('%H:%M')} ({nat_dur//60}h {nat_dur%60:02d}m)"
            else:
                sun_str = f"{plan.natural_daylight_hours}h"

            # Morning Light
            if plan.morning_session:
                m_dur = int(plan.morning_session.duration.total_seconds() / 60)
                shift_note = ""
                if plan.morning_displaced_duration.total_seconds() > 0:
                    s_dur = int(plan.morning_displaced_duration.total_seconds() / 60)
                    shift_note = f"<br>*(shifted {s_dur//60}h {s_dur%60:02d}m to evening)*"
                morn_str = f"{plan.morning_session.start.strftime('%H:%M')} – {plan.morning_session.end.strftime('%H:%M')} ({m_dur//60}h {m_dur%60:02d}m){shift_note}"
            elif plan.morning_displaced_duration.total_seconds() > 0:
                s_dur = int(plan.morning_displaced_duration.total_seconds() / 60)
                morn_str = f"Off *(all {s_dur//60}h {s_dur%60:02d}m shifted to evening)*"
            else:
                morn_str = "Off *(Sunlight exceeds target)*" if plan.supplementary_hours <= 0 else "Off"

            # Evening Light
            if plan.evening_session:
                e_dur = int(plan.evening_session.duration.total_seconds() / 60)
                inc_note = ""
                if plan.morning_displaced_duration.total_seconds() > 0:
                    s_dur = int(plan.morning_displaced_duration.total_seconds() / 60)
                    inc_note = f"<br>*(includes {s_dur//60}h {s_dur%60:02d}m morning shift)*"
                eve_str = f"{plan.evening_session.start.strftime('%H:%M')} – {plan.evening_session.end.strftime('%H:%M')} ({e_dur//60}h {e_dur%60:02d}m){inc_note}"
            else:
                eve_str = "Off *(Sunlight exceeds target)*" if plan.supplementary_hours <= 0 else "Off"

            # Total Light
            tot_dur = int(plan.actual_photoperiod.total_seconds() / 60)
            tot_pct = int(min(100, round((tot_dur / (target_hours * 60)) * 100))) if target_hours > 0 else 100
            tot_str = f"**{tot_dur//60}h {tot_dur%60:02d}m** ({tot_pct}%)"

            rows.append(f"| {label} | {morn_str} | {sun_str} | {eve_str} | {tot_str} |")

        return "\n".join(rows)

    def get_seasonal_preview_text(
        self,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
        ref_year: int | None = None,
    ) -> str:
        """Format the complete seasonal preview with SVG timeline, text ruler, and exact table."""
        year = ref_year or datetime.now(self.tz).year

        earliest_info = self.get_annual_earliest_turn_on(
            target_hours=target_hours,
            mode=mode,
            morning_split_pct=morning_split_pct,
            overlap_hours=overlap_hours,
            earliest_start=earliest_start,
            latest_end=latest_end,
            year=year,
        )

        svg_chart = self.generate_svg_timeline_b64(
            target_hours=target_hours,
            mode=mode,
            morning_split_pct=morning_split_pct,
            overlap_hours=overlap_hours,
            earliest_start=earliest_start,
            latest_end=latest_end,
            year=year,
        )

        banner = []
        if earliest_info["is_clamped"]:
            banner.append(
                f"**Earliest Annual Turn-On**: **{earliest_info['effective_time']}** "
                f"*(astronomical schedule: {earliest_info['unclamped_time']} — held back by morning cut-off)*\n"
                f"**Sleep Protection Active**: All lighting before {earliest_info['cutoff_time']} is prevented and moved to the evening."
            )
        else:
            banner.append(
                f"**Earliest Annual Turn-On**: **{earliest_info['effective_time']}**"
            )

        return "\n\n".join([
            "\n".join(banner),
            svg_chart,
        ])

    def get_current_status(
        self,
        now: datetime,
        target_hours: float,
        mode: str = "both",
        morning_split_pct: float = 50.0,
        overlap_hours: float = 1.0,
        is_enabled: bool = True,
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
    ) -> str:
        """Determine current status string observing enabled switch and sleep cut-offs."""
        if not is_enabled:
            return "disabled"

        today_plan = self.get_daily_photoperiod(
            now.date(),
            target_hours=target_hours,
            mode=mode,
            morning_split_pct=morning_split_pct,
            overlap_hours=overlap_hours,
            earliest_start=earliest_start,
            latest_end=latest_end,
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
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
    ) -> NextSession:
        """Find upcoming supplementary session observing morning/evening cut-offs."""
        for day_offset in range(3):
            check_date = now.date() + timedelta(days=day_offset)
            plan = self.get_daily_photoperiod(
                check_date,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
                earliest_start=earliest_start,
                latest_end=latest_end,
            )

            if plan.morning_session and plan.morning_session.end > now:
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
        earliest_start: time | str | None = None,
        latest_end: time | str | None = None,
        year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a 12-month breakdown (15th of each month) of solar and supplementary light."""
        if year is None:
            year = datetime.now(self.tz).year

        months_data = []
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]

        for m_idx in range(1, 13):
            sample_date = date(year, m_idx, 15)
            plan = self.get_daily_photoperiod(
                sample_date,
                target_hours=target_hours,
                mode=mode,
                morning_split_pct=morning_split_pct,
                overlap_hours=overlap_hours,
                earliest_start=earliest_start,
                latest_end=latest_end,
            )

            months_data.append({
                "month": m_idx,
                "name": month_names[m_idx - 1],
                "natural_hours": plan.natural_daylight_hours,
                "supplementary_hours": plan.actual_supplementary_hours,
                "target_hours": plan.target_hours,
                "sunrise": plan.sunrise.strftime("%H:%M") if plan.sunrise else None,
                "sunset": plan.sunset.strftime("%H:%M") if plan.sunset else None,
                "morning_hours": plan.morning_session.duration_hours if plan.morning_session else 0.0,
                "evening_hours": plan.evening_session.duration_hours if plan.evening_session else 0.0,
            })

        return months_data
