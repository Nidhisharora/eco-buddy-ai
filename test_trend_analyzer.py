"""
Tests for Carbon Footprint Trend Analyzer Engine.

Covers: linear regression, trend classification, seasonal patterns,
anomaly detection, category trends, forecasting, insights, and
full report generation with edge cases.
"""

import math
import statistics
import pytest
from src.carbon.trend_analyzer import (
    AssessmentRecord,
    TrendDirection,
    InsightSeverity,
    Season,
    TrendResult,
    SeasonalPattern,
    AnomalyRecord,
    ForecastPoint,
    CategoryTrend,
    Insight,
    TrendReport,
    _get_season,
    _date_to_month_index,
    _month_index_to_label,
    _linear_regression,
    _classify_trend,
    _interpret_trend,
    analyse_overall_trend,
    analyse_seasonal_patterns,
    detect_anomalies,
    analyse_category_trends,
    generate_forecasts,
    generate_insights,
    generate_trend_report,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_record(date: str, fp: float, score: int = 50, transport: str = "Car",
                 distance: float = 15.0, electricity: float = 200.0,
                 diet: str = "Vegetarian", flights: int = 0) -> AssessmentRecord:
    return AssessmentRecord(
        date=date, transport=transport, distance=distance,
        electricity=electricity, diet=diet, flights=flights,
        footprint=fp, eco_score=score,
    )


def _make_series(n: int, base: float = 4000, trend: float = -20,
                 seasonal_amp: float = 200, noise_std: float = 100) -> list[AssessmentRecord]:
    """Generate n monthly records with trend + seasonality + noise."""
    import random
    random.seed(42)
    records = []
    for i in range(n):
        month = (i % 12) + 1
        year = 2024 + i // 12
        fp = base + trend * i + seasonal_amp * math.sin(2 * math.pi * month / 12) + random.gauss(0, noise_std)
        fp = max(100, fp)
        score = max(10, min(100, int(100 / (1 + math.exp((fp - 4000) / 1000)))))
        records.append(_make_record(f"{year}-{month:02d}-15", round(fp, 2), score))
    return records


# ─── Unit: helpers ──────────────────────────────────────────────────────────

class TestGetSeason:
    def test_spring(self):
        assert _get_season("2024-04-10") == Season.SPRING

    def test_summer(self):
        assert _get_season("2024-07-20") == Season.SUMMER

    def test_autumn(self):
        assert _get_season("2024-10-05") == Season.AUTUMN

    def test_winter(self):
        assert _get_season("2024-01-15") == Season.WINTER

    def test_invalid_date_returns_spring(self):
        assert _get_season("invalid") == Season.SPRING

    def test_year_prefix(self):
        assert _get_season("2025-12-01") == Season.WINTER


class TestMonthIndex:
    def test_same_month(self):
        assert _date_to_month_index("2024-06-15", "2024-06-01") == 0

    def test_one_month_later(self):
        assert _date_to_month_index("2024-07-15", "2024-06-01") == 1

    def test_year_crossing(self):
        assert _date_to_month_index("2025-02-10", "2024-11-01") == 3

    def test_invalid_returns_zero(self):
        assert _date_to_month_index("bad", "2024-01-01") == 0

    def test_label_round_trip(self):
        label = _month_index_to_label(6, "2024-01-01")
        assert "2024" in label or "Jul" in label or "Aug" in label


class TestMonthIndexToLabel:
    def test_label_format(self):
        label = _month_index_to_label(0, "2024-01-01")
        assert "Jan" in label

    def test_label_year_wrap(self):
        label = _month_index_to_label(13, "2024-01-01")
        assert "2025" in label

    def test_invalid_returns_placeholder(self):
        label = _month_index_to_label(0, "bad-date")
        assert "Month" in label


# ─── Unit: linear regression ────────────────────────────────────────────────

class TestLinearRegression:
    def test_perfect_positive(self):
        x = [0, 1, 2, 3, 4]
        y = [10, 20, 30, 40, 50]
        slope, intercept, r2, _ = _linear_regression(x, y)
        assert slope == pytest.approx(10.0, abs=0.01)
        assert intercept == pytest.approx(10.0, abs=0.01)
        assert r2 == pytest.approx(1.0, abs=0.01)

    def test_perfect_negative(self):
        x = [0, 1, 2, 3]
        y = [100, 80, 60, 40]
        slope, intercept, r2, _ = _linear_regression(x, y)
        assert slope == pytest.approx(-20.0, abs=0.01)
        assert r2 == pytest.approx(1.0, abs=0.01)

    def test_noisy_data(self):
        x = [0, 1, 2, 3, 4, 5]
        y = [10, 12, 9, 15, 13, 18]
        slope, intercept, r2, _ = _linear_regression(x, y)
        assert slope > 0  # generally upward
        assert 0 < r2 < 1

    def test_single_point(self):
        slope, intercept, r2, _ = _linear_regression([2], [50])
        assert r2 == 0.0

    def test_empty(self):
        slope, intercept, r2, _ = _linear_regression([], [])
        assert slope == 0.0


# ─── Unit: trend classification ─────────────────────────────────────────────

class TestClassifyTrend:
    def test_improving(self):
        vals = [100, 90, 80, 70, 60]
        assert _classify_trend(-10, 0.95, vals) == TrendDirection.IMPROVING

    def test_worsening(self):
        vals = [60, 70, 80, 90, 100]
        assert _classify_trend(10, 0.95, vals) == TrendDirection.WORSENING

    def test_stable(self):
        vals = [50, 50, 50, 50, 50]
        assert _classify_trend(0, 1.0, vals) == TrendDirection.STABLE

    def test_volatile(self):
        import random
        random.seed(7)
        vals = [random.uniform(10, 100) for _ in range(20)]
        assert _classify_trend(0.5, 0.1, vals) == TrendDirection.VOLATILE

    def test_empty(self):
        assert _classify_trend(0, 0, []) == TrendDirection.STABLE


class TestInterpretTrend:
    def test_improving_strong(self):
        result = _interpret_trend(TrendDirection.IMPROVING, -500, 0.8)
        assert "decreasing" in result.lower()

    def test_worsening(self):
        result = _interpret_trend(TrendDirection.WORSENING, 300, 0.6)
        assert "increasing" in result.lower()

    def test_stable(self):
        result = _interpret_trend(TrendDirection.STABLE, 0, 1.0)
        assert "stable" in result.lower()

    def test_volatile(self):
        result = _interpret_trend(TrendDirection.VOLATILE, 0, 0.1)
        assert "variab" in result.lower()


# ─── Unit: overall trend ───────────────────────────────────────────────────

class TestAnalyseOverallTrend:
    def test_improving_series(self):
        records = [
            _make_record("2024-01-01", 5000),
            _make_record("2024-02-01", 4800),
            _make_record("2024-03-01", 4600),
            _make_record("2024-04-01", 4400),
            _make_record("2024-05-01", 4200),
        ]
        trend = analyse_overall_trend(records)
        assert trend.direction == TrendDirection.IMPROVING
        assert trend.slope_per_month < 0

    def test_worsening_series(self):
        records = [
            _make_record("2024-01-01", 2000),
            _make_record("2024-02-01", 2200),
            _make_record("2024-03-01", 2400),
            _make_record("2024-04-01", 2600),
            _make_record("2024-05-01", 2800),
        ]
        trend = analyse_overall_trend(records)
        assert trend.direction == TrendDirection.WORSENING
        assert trend.slope_per_month > 0

    def test_single_record(self):
        trend = analyse_overall_trend([_make_record("2024-01-01", 3000)])
        assert trend.direction == TrendDirection.STABLE

    def test_empty(self):
        trend = analyse_overall_trend([])
        assert trend.direction == TrendDirection.STABLE
        assert trend.interpretation == "Insufficient data for trend analysis."

    def test_to_dict(self):
        trend = analyse_overall_trend([
            _make_record("2024-01-01", 4000),
            _make_record("2024-02-01", 3900),
        ])
        d = trend.to_dict()
        assert "direction" in d
        assert "r_squared" in d


# ─── Unit: seasonal patterns ────────────────────────────────────────────────

class TestSeasonalPatterns:
    def test_basic(self):
        records = [
            _make_record("2024-01-15", 4500),
            _make_record("2024-04-15", 3800),
            _make_record("2024-07-15", 5000),
            _make_record("2024-10-15", 4200),
        ]
        patterns = analyse_seasonal_patterns(records)
        assert len(patterns) == 4

    def test_insufficient_data(self):
        records = [_make_record("2024-01-01", 4000)]
        assert analyse_seasonal_patterns(records) == []

    def test_same_season_grouping(self):
        records = [
            _make_record("2024-01-10", 4000),
            _make_record("2024-01-20", 4200),
            _make_record("2024-07-10", 5000),
            _make_record("2024-07-20", 5200),
        ]
        patterns = analyse_seasonal_patterns(records)
        seasons = {p.season for p in patterns}
        assert Season.WINTER in seasons
        assert Season.SUMMER in seasons

    def test_to_dict(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000 + m * 50) for m in range(1, 13)]
        patterns = analyse_seasonal_patterns(records)
        for p in patterns:
            d = p.to_dict()
            assert "season" in d
            assert "avg_footprint" in d


# ─── Unit: anomaly detection ────────────────────────────────────────────────

class TestAnomalyDetection:
    def test_spike_detected(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        records.append(_make_record("2024-06-15", 8000))  # big spike
        anomalies = detect_anomalies(records, threshold_multiplier=1.5)
        assert any(a.is_spike for a in anomalies)

    def test_no_anomalies_in平稳_series(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        anomalies = detect_anomalies(records, threshold_multiplier=3.0)
        # Very uniform data — no anomalies expected
        assert len(anomalies) <= 1

    def test_insufficient_data(self):
        assert detect_anomalies([_make_record("2024-01-01", 4000)]) == []

    def test_category_hint_flights(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        records.append(_make_record("2024-06-15", 8000, flights=5))
        anomalies = detect_anomalies(records, threshold_multiplier=1.5)
        flight_anomalies = [a for a in anomalies if a.category_hint == "flights"]
        assert len(flight_anomalies) >= 1

    def test_to_dict(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        records.append(_make_record("2024-06-15", 9000))
        anomalies = detect_anomalies(records, threshold_multiplier=1.5)
        for a in anomalies:
            d = a.to_dict()
            assert "date" in d
            assert "is_spike" in d


# ─── Unit: category trends ─────────────────────────────────────────────────

class TestCategoryTrends:
    def test_basic(self):
        records = []
        for m in range(1, 13):
            fp = 3000 + m * 100
            records.append(_make_record(
                f"2024-{m:02d}-15", fp, distance=10 + m,
                electricity=150 + m * 10,
            ))
        trends = analyse_category_trends(records)
        assert len(trends) == 4
        cats = {t.category for t in trends}
        assert "Transport" in cats
        assert "Electricity" in cats

    def test_insufficient_data(self):
        records = [_make_record("2024-01-01", 4000)]
        assert analyse_category_trends(records) == []

    def test_contributions_sum_to_100(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        trends = analyse_category_trends(records)
        total = sum(t.contribution_to_total for t in trends)
        assert total == pytest.approx(100.0, abs=1.0)

    def test_to_dict(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        trends = analyse_category_trends(records)
        for t in trends:
            d = t.to_dict()
            assert "category" in d
            assert "direction" in d


# ─── Unit: forecasts ────────────────────────────────────────────────────────

class TestForecasts:
    def test_basic_forecast(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000 - m * 20) for m in range(1, 13)]
        forecasts = generate_forecasts(records, months_ahead=6)
        assert len(forecasts) == 18  # 6 months × 3 scenarios

    def test_scenarios_present(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 7)]
        forecasts = generate_forecasts(records, months_ahead=3)
        scenarios = {f.scenario for f in forecasts}
        assert "current_trend" in scenarios
        assert "optimistic" in scenarios
        assert "pessimistic" in scenarios

    def test_optimistic_lower_than_pessimistic(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        forecasts = generate_forecasts(records, months_ahead=6)
        by_date = {}
        for f in forecasts:
            by_date.setdefault(f.date_label, {})[f.scenario] = f.predicted_footprint
        for label, scenarios in by_date.items():
            if "optimistic" in scenarios and "pessimistic" in scenarios:
                assert scenarios["optimistic"] <= scenarios["pessimistic"]

    def test_confidence_bands_widen(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        forecasts = generate_forecasts(records, months_ahead=6)
        ct = [f for f in forecasts if f.scenario == "current_trend"]
        if len(ct) >= 2:
            band_early = ct[0].confidence_upper - ct[0].confidence_lower
            band_late = ct[-1].confidence_upper - ct[-1].confidence_lower
            assert band_late >= band_early

    def test_insufficient_data(self):
        assert generate_forecasts([]) == []

    def test_to_dict(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 7)]
        forecasts = generate_forecasts(records, months_ahead=2)
        for f in forecasts:
            d = f.to_dict()
            assert "predicted_footprint" in d
            assert "confidence_lower" in d


# ─── Unit: insights ─────────────────────────────────────────────────────────

class TestInsights:
    def test_worsening_trend_generates_warning(self):
        trend = TrendResult(
            direction=TrendDirection.WORSENING, slope_per_month=50,
            slope_per_year=600, r_squared=0.8, intercept=3000,
            pct_change_monthly=1.5, interpretation="Getting worse.",
        )
        insights = generate_insights(trend, [], [], [], 4000)
        assert any(i.severity == InsightSeverity.WARNING for i in insights)

    def test_improving_trend_generates_positive(self):
        trend = TrendResult(
            direction=TrendDirection.IMPROVING, slope_per_month=-30,
            slope_per_year=-360, r_squared=0.7, intercept=5000,
            pct_change_monthly=-0.8, interpretation="Getting better.",
        )
        insights = generate_insights(trend, [], [], [], 3500)
        assert any(i.severity == InsightSeverity.POSITIVE for i in insights)

    def test_high_footprint_insight(self):
        trend = TrendResult(
            direction=TrendDirection.STABLE, slope_per_month=0,
            slope_per_year=0, r_squared=0.5, intercept=4000,
            pct_change_monthly=0, interpretation="Stable.",
        )
        insights = generate_insights(trend, [], [], [], 7000)
        assert any("High Overall Footprint" in i.title for i in insights)

    def test_low_footprint_insight(self):
        trend = TrendResult(
            direction=TrendDirection.STABLE, slope_per_month=0,
            slope_per_year=0, r_squared=0.5, intercept=2000,
            pct_change_monthly=0, interpretation="Stable.",
        )
        insights = generate_insights(trend, [], [], [], 2000)
        assert any("Below-Average" in i.title for i in insights)

    def test_seasonal_insight(self):
        trend = TrendResult(
            direction=TrendDirection.STABLE,            slope_per_month=0,
            slope_per_year=0, r_squared=0.5, intercept=4000,
            pct_change_monthly=0, interpretation="Stable.",
        )
        seasonal = [
            SeasonalPattern(Season.SUMMER, 5000, 50, 3, 800),
            SeasonalPattern(Season.WINTER, 3500, 65, 3, -700),
        ]
        insights = generate_insights(trend, seasonal, [], [], 4000)
        assert any("Season" in i.title or "Summer" in i.title for i in insights)

    def test_to_dict(self):
        trend = TrendResult(
            direction=TrendDirection.STABLE, slope_per_month=0,
            slope_per_year=0, r_squared=0.5, intercept=4000,
            pct_change_monthly=0, interpretation="Stable.",
        )
        insights = generate_insights(trend, [], [], [], 4000)
        for i in insights:
            d = i.to_dict()
            assert "title" in d
            assert "severity" in d


# ─── Unit: full report ─────────────────────────────────────────────────────

class TestGenerateTrendReport:
    def test_full_report_structure(self):
        records = _make_series(24)
        report = generate_trend_report(records, user_id=1, goal_target=4000)
        assert report.total_assessments == 24
        assert report.analysis_period_months > 0
        assert report.overall_trend is not None
        assert len(report.footprint_timeline) == 24
        assert len(report.category_trends) > 0
        assert len(report.insights) > 0

    def test_report_with_goal(self):
        records = _make_series(12, base=5000, trend=-50)
        report = generate_trend_report(records, user_id=2, goal_target=3500)
        assert report.goal_target == 3500
        assert report.goal_proximity_pct is not None

    def test_report_without_goal(self):
        records = _make_series(12)
        report = generate_trend_report(records, user_id=3)
        assert report.goal_target is None
        assert report.goal_proximity_pct is None

    def test_empty_records(self):
        report = generate_trend_report([], user_id=99)
        assert report.total_assessments == 0
        assert report.date_range == "No data"
        assert len(report.footprint_timeline) == 0

    def test_single_record(self):
        records = [_make_record("2024-06-01", 4500)]
        report = generate_trend_report(records, user_id=1)
        assert report.total_assessments == 1
        assert report.avg_footprint == 4500

    def test_to_dict(self):
        records = _make_series(12)
        report = generate_trend_report(records, user_id=1)
        d = report.to_dict()
        assert "overall_trend" in d
        assert "category_trends" in d
        assert "insights" in d
        assert "summary" in d

    def test_forecast_in_report(self):
        records = _make_series(12)
        report = generate_trend_report(records, user_id=1, forecast_months=6)
        assert len(report.forecasts) == 18  # 6 × 3 scenarios

    def test_summary_stats(self):
        records = _make_series(12)
        report = generate_trend_report(records, user_id=1)
        assert report.avg_footprint > 0
        assert report.median_footprint > 0
        assert report.min_footprint <= report.avg_footprint <= report.max_footprint


# ─── Edge cases ─────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_all_same_footprint(self):
        records = [_make_record(f"2024-{m:02d}-15", 4000) for m in range(1, 13)]
        report = generate_trend_report(records)
        assert report.overall_trend.direction == TrendDirection.STABLE
        assert report.std_footprint == 0.0

    def test_very_high_values(self):
        records = [_make_record(f"2024-{m:02d}-15", 50000) for m in range(1, 7)]
        report = generate_trend_report(records)
        assert report.avg_footprint == 50000

    def test_very_low_values(self):
        records = [_make_record(f"2024-{m:02d}-15", 100) for m in range(1, 7)]
        report = generate_trend_report(records)
        assert report.avg_footprint == 100

    def test_unsorted_input(self):
        records = [
            _make_record("2024-03-15", 3800),
            _make_record("2024-01-15", 4200),
            _make_record("2024-02-15", 4000),
        ]
        report = generate_trend_report(records)
        assert report.total_assessments == 3
        # Should be sorted internally
        dates = [t["date"] for t in report.footprint_timeline]
        assert dates == sorted(dates)

    def test_negative_slope_r_squared(self):
        """Ensure R² is always non-negative."""
        x = [0, 1, 2, 3, 4]
        y = [50, 50, 50, 50, 50]
        _, _, r2, _ = _linear_regression(x, y)
        assert r2 >= 0

    def test_forecast_non_negative(self):
        records = [_make_record(f"2024-{m:02d}-15", 100) for m in range(1, 7)]
        forecasts = generate_forecasts(records, months_ahead=6)
        for f in forecasts:
            assert f.predicted_footprint >= 0
