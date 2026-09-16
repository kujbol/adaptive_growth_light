"""Unit tests for solar photoperiod calculation engine."""

from datetime import date, datetime, timedelta
import zoneinfo
import pytest

from custom_components.adaptive_growth_light.solar import (
    SolarCalculator,
    SessionWindow,
    DailyPhotoperiod,
)

# Warsaw coordinates
WARSAW_LAT = 52.2297
WARSAW_LON = 21.0122
TZ_WARSAW = zoneinfo.ZoneInfo("Europe/Warsaw")


@pytest.fixture
def warsaw_calculator() -> SolarCalculator:
    return SolarCalculator(
        latitude=WARSAW_LAT,
        longitude=WARSAW_LON,
        elevation=100.0,
        tz=TZ_WARSAW,
    )


def test_session_window_duration_and_active():
    start = datetime(2026, 6, 21, 5, 0, tzinfo=TZ_WARSAW)
    end = datetime(2026, 6, 21, 7, 30, tzinfo=TZ_WARSAW)
    window = SessionWindow(start=start, end=end)

    assert window.duration == timedelta(hours=2, minutes=30)
    assert window.duration_hours == 2.5
    assert window.is_active(datetime(2026, 6, 21, 6, 0, tzinfo=TZ_WARSAW)) is True
    assert window.is_active(datetime(2026, 6, 21, 4, 59, tzinfo=TZ_WARSAW)) is False
    assert window.is_active(datetime(2026, 6, 21, 7, 30, tzinfo=TZ_WARSAW)) is False


def test_summer_solstice_photoperiod(warsaw_calculator: SolarCalculator):
    # In Warsaw on June 21, daylight is ~16.8 hours
    summer_date = date(2026, 6, 21)
    plan = warsaw_calculator.get_daily_photoperiod(
        calc_date=summer_date,
        target_hours=14.0,
        mode="both",
        morning_split_pct=50.0,
        overlap_hours=1.0,
    )

    assert plan.natural_daylight_hours > 16.0
    # Natural daylight exceeds 14h target -> 0 supplementary light needed
    assert plan.supplementary_hours == 0.0
    assert plan.morning_session is None
    assert plan.evening_session is None


def test_winter_solstice_photoperiod(warsaw_calculator: SolarCalculator):
    # In Warsaw on December 21, daylight is ~7.7 - 7.8 hours
    winter_date = date(2026, 12, 21)
    plan = warsaw_calculator.get_daily_photoperiod(
        calc_date=winter_date,
        target_hours=14.0,
        mode="both",
        morning_split_pct=50.0,
        overlap_hours=1.0,
    )

    assert 7.0 < plan.natural_daylight_hours < 8.5
    # Supplementary light must bridge the gap to 14 hours
    expected_supp = round(14.0 - plan.natural_daylight_hours, 2)
    assert abs(plan.supplementary_hours - expected_supp) < 0.05
    assert plan.morning_session is not None
    assert plan.evening_session is not None

    # In 50/50 mode, morning and evening durations are equal
    assert abs(plan.morning_session.duration_hours - plan.evening_session.duration_hours) < 0.02
    total_session_hours = plan.morning_session.duration_hours + plan.evening_session.duration_hours
    assert abs(total_session_hours - plan.supplementary_hours) < 0.05


def test_modes_morning_evening_both(warsaw_calculator: SolarCalculator):
    winter_date = date(2026, 1, 15)

    # Morning only
    plan_morn = warsaw_calculator.get_daily_photoperiod(
        calc_date=winter_date, target_hours=14.0, mode="morning", overlap_hours=0.5
    )
    assert plan_morn.morning_session is not None
    assert plan_morn.evening_session is None
    assert plan_morn.morning_session.duration_hours == plan_morn.supplementary_hours

    # Evening only
    plan_eve = warsaw_calculator.get_daily_photoperiod(
        calc_date=winter_date, target_hours=14.0, mode="evening", overlap_hours=0.5
    )
    assert plan_eve.morning_session is None
    assert plan_eve.evening_session is not None
    assert plan_eve.evening_session.duration_hours == plan_eve.supplementary_hours

    # Both with 70/30 split
    plan_split = warsaw_calculator.get_daily_photoperiod(
        calc_date=winter_date, target_hours=14.0, mode="both", morning_split_pct=70.0
    )
    assert plan_split.morning_session is not None
    assert plan_split.evening_session is not None
    assert plan_split.morning_session.duration_hours > plan_split.evening_session.duration_hours
    assert abs(plan_split.morning_session.duration_hours - round(plan_split.supplementary_hours * 0.7, 2)) < 0.05


def test_daylight_overlap_transition(warsaw_calculator: SolarCalculator):
    winter_date = date(2026, 12, 1)
    overlap = 1.5  # 1.5 hours overlap

    plan = warsaw_calculator.get_daily_photoperiod(
        calc_date=winter_date,
        target_hours=14.0,
        mode="both",
        morning_split_pct=50.0,
        overlap_hours=overlap,
    )

    sunrise = plan.sunrise
    sunset = plan.sunset
    assert sunrise is not None
    assert sunset is not None

    # Morning session must end exactly at sunrise + overlap
    expected_m_end = sunrise + timedelta(hours=overlap)
    assert plan.morning_session.end == expected_m_end
    # Morning session start must be end - morning duration
    assert plan.morning_session.start == expected_m_end - plan.morning_session.duration

    # Evening session must start exactly at sunset - overlap
    expected_e_start = sunset - timedelta(hours=overlap)
    assert plan.evening_session.start == expected_e_start
    # Evening session end must be start + evening duration
    assert plan.evening_session.end == expected_e_start + plan.evening_session.duration


def test_current_status_and_next_session(warsaw_calculator: SolarCalculator):
    winter_date = date(2026, 12, 21)
    plan = warsaw_calculator.get_daily_photoperiod(
        winter_date, target_hours=14.0, mode="both", morning_split_pct=50.0, overlap_hours=1.0
    )

    m_start = plan.morning_session.start
    m_end = plan.morning_session.end
    e_start = plan.evening_session.start
    e_end = plan.evening_session.end

    # 1. During morning session
    now_morn = m_start + timedelta(minutes=10)
    assert warsaw_calculator.get_current_status(
        now_morn, target_hours=14.0, mode="both", morning_split_pct=50.0, overlap_hours=1.0
    ) == "supplementing_morning"

    # 2. During midday
    noon = datetime.combine(winter_date, datetime.min.time(), tzinfo=TZ_WARSAW) + timedelta(hours=12)
    assert warsaw_calculator.get_current_status(
        noon, target_hours=14.0, mode="both", morning_split_pct=50.0, overlap_hours=1.0
    ) == "daylight_active"

    # 3. Disabled flag
    assert warsaw_calculator.get_current_status(
        now_morn, target_hours=14.0, is_enabled=False
    ) == "disabled"

    # 4. Next session lookup: 1 hour before morning session starts
    before_morn = m_start - timedelta(hours=1)
    next_s = warsaw_calculator.get_next_session(
        before_morn, target_hours=14.0, mode="both", morning_split_pct=50.0, overlap_hours=1.0
    )
    assert next_s.session_type == "morning"
    assert next_s.start == m_start
    assert abs(next_s.seconds_until - 3600.0) < 1.0


def test_seasonal_matrix_12_months(warsaw_calculator: SolarCalculator):
    matrix = warsaw_calculator.get_seasonal_matrix(
        target_hours=14.0,
        mode="both",
        morning_split_pct=50.0,
        overlap_hours=1.0,
        year=2026,
    )

    assert len(matrix) == 12
    # Check month sequence
    months = [item["month"] for item in matrix]
    assert months == list(range(1, 13))

    # June (index 5) should have maximum natural daylight and 0 supplementary hours
    june = matrix[5]
    assert june["natural_hours"] > 16.0
    assert june["supplementary_hours"] == 0.0

    # December (index 11) should have minimum natural daylight and positive supplementary hours
    dec = matrix[11]
    assert dec["natural_hours"] < 8.5
    assert dec["supplementary_hours"] > 5.5
    assert abs((dec["natural_hours"] + dec["supplementary_hours"]) - 14.0) < 0.1


def test_polar_coordinates_safety():
    # Longyearbyen (Svalbard: 78.22° N)
    svalbard_calc = SolarCalculator(latitude=78.22, longitude=15.65)
    # Midnight sun in June
    plan_summer = svalbard_calc.get_daily_photoperiod(date(2026, 6, 21), target_hours=14.0)
    assert plan_summer.natural_daylight_hours == 24.0
    assert plan_summer.supplementary_hours == 0.0

    # Polar night in December
    plan_winter = svalbard_calc.get_daily_photoperiod(date(2026, 12, 21), target_hours=14.0)
    assert plan_winter.natural_daylight_hours == 0.0
    assert plan_winter.supplementary_hours == 14.0
