"""
Carbon Trend Analyzer — Streamlit Page

Visualise assessment history trends, seasonal patterns, anomaly detection,
forecasts, and actionable insights with interactive Plotly charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import math
from datetime import datetime

from src.carbon.trend_analyzer import (
    AssessmentRecord,
    TrendDirection,
    InsightSeverity,
    Season,
    generate_trend_report,
)

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Carbon Trend Analyzer", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .insight-critical { background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; border-radius: 8px; margin: 8px 0; }
    .insight-warning  { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 8px; margin: 8px 0; }
    .insight-info     { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px; border-radius: 8px; margin: 8px 0; }
    .insight-positive { background: #f0fdf4; border-left: 4px solid #22c55e; padding: 12px; border-radius: 8px; margin: 8px 0; }
    .trend-up   { color: #ef4444; font-weight: 700; }
    .trend-down { color: #22c55e; font-weight: 700; }
    .trend-flat { color: #6b7280; font-weight: 700; }
    .anomaly-card { background: #fefce8; border: 1px solid #facc15; border-radius: 10px; padding: 14px; margin: 8px 0; }
    .goal-bar { height: 20px; border-radius: 10px; background: #e5e7eb; overflow: hidden; margin: 6px 0; }
    .goal-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, #22c55e, #16a34a); transition: width 0.4s; }
</style>
""", unsafe_allow_html=True)


# ─── Sample Data Generator ──────────────────────────────────────────────────
def _generate_sample_records(count: int = 24) -> list[AssessmentRecord]:
    """Generate sample assessment records for demo purposes."""
    import random
    random.seed(42)
    records = []
    base_fp = 4500
    base_score = 55

    for i in range(count):
        month_offset = i
        year = 2024 + (month_offset // 12)
        month = (month_offset % 12) + 1
        date_str = f"{year}-{month:02d}-15"

        # Add a slight downward trend + noise + seasonality
        trend = -30 * i
        seasonal = 300 * math.sin(2 * math.pi * month / 12)
        noise = random.gauss(0, 200)

        # Spike at month 8
        spike = 800 if i == 8 else 0
        # Spike at month 15
        spike += 600 if i == 15 else 0

        fp = max(500, base_fp + trend + seasonal + noise + spike)
        score = max(10, min(100, int(100 / (1 + math.exp((fp - 4000) / 1000)))))

        transport_options = ["Car", "Public Transport", "Bike", "Walking"]
        diet_options = ["Vegetarian", "Non-Vegetarian", "Vegan", "Omnivore"]

        records.append(AssessmentRecord(
            date=date_str,
            transport=random.choice(transport_options),
            distance=random.uniform(5, 30),
            electricity=random.uniform(100, 400),
            diet=random.choice(diet_options),
            flights=random.randint(0, 3),
            footprint=round(fp, 2),
            eco_score=score,
        ))
    return records


# ─── Sidebar Controls ───────────────────────────────────────────────────────
st.sidebar.header("📈 Trend Analyzer Settings")

data_source = st.sidebar.radio(
    "Data source",
    ["Sample data (demo)", "Use session data"],
)

if data_source == "Use session data" and "assessments" in st.session_state:
    raw = st.session_state["assessments"]
    records = []
    for row in raw:
        # Unpack the tuple from get_assessments()
        try:
            rec = AssessmentRecord(
                date=str(row[2]) if row[2] else str(row[1]),
                transport=str(row[3]) if len(row) > 3 else "",
                distance=float(row[4]) if len(row) > 4 else 0,
                electricity=float(row[5]) if len(row) > 5 else 0,
                diet=str(row[6]) if len(row) > 6 else "",
                flights=int(row[7]) if len(row) > 7 else 0,
                footprint=float(row[8]) if len(row) > 8 else 0,
                eco_score=int(row[9]) if len(row) > 9 else 0,
            )
            records.append(rec)
        except (IndexError, TypeError, ValueError):
            continue
    if not records:
        st.sidebar.info("No valid assessment records found. Using sample data.")
        records = _generate_sample_records()
else:
    records = _generate_sample_records()

num_records = st.sidebar.slider("Sample records to generate", 6, 60, len(records))
if data_source == "Sample data (demo)":
    records = _generate_sample_records(num_records)

forecast_months = st.sidebar.slider("Forecast horizon (months)", 3, 24, 12)
goal_target = st.sidebar.number_input(
    "Annual carbon goal (kg CO₂)", 0.0, 20000.0, 4000.0, 100.0,
    help="Set to 0 to disable goal tracking.",
)
goal = goal_target if goal_target > 0 else None

# ─── Run Analysis ───────────────────────────────────────────────────────────
report = generate_trend_report(records, user_id=1, goal_target=goal, forecast_months=forecast_months)

# ─── Page Title ─────────────────────────────────────────────────────────────
st.title("📈 Carbon Footprint Trend Analyzer")
st.markdown(
    f"**{report.total_assessments}** assessments analysed "
    f"from **{report.date_range}** "
    f"({report.analysis_period_months} months)"
)

# ─── Summary Metrics ────────────────────────────────────────────────────────
st.subheader("📊 Summary Statistics")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Avg Footprint", f"{report.avg_footprint:,.0f} kg")
with c2:
    st.metric("Median Footprint", f"{report.median_footprint:,.0f} kg")
with c3:
    st.metric("Std Deviation", f"{report.std_footprint:,.0f} kg")
with c4:
    st.metric("Min / Max", f"{report.min_footprint:,.0f} / {report.max_footprint:,.0f}")
with c5:
    st.metric("Avg Eco Score", f"{report.avg_eco_score:.0f}/100")

# ─── Goal Tracking ──────────────────────────────────────────────────────────
if report.goal_target and report.goal_target > 0:
    st.subheader("🎯 Goal Tracking")
    proximity = report.goal_proximity_pct or 0
    months_to = report.months_to_goal

    g1, g2, g3 = st.columns([2, 1, 1])
    with g1:
        st.markdown(f"**Target:** {report.goal_target:,.0f} kg CO₂/year")
        st.markdown(
            f'<div class="goal-bar"><div class="goal-fill" style="width:{min(100, proximity):.0f}%"></div></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{proximity:.1f}% toward goal")
    with g2:
        if months_to:
            st.metric("Months to Goal", f"{months_to:.0f}")
        else:
            st.metric("Months to Goal", "N/A")
    with g3:
        trend_icon = "📈" if report.overall_trend.direction == TrendDirection.WORSENING else "📉"
        st.metric("Trend", f"{trend_icon} {report.overall_trend.direction.value.title()}")

# ─── Overall Trend ──────────────────────────────────────────────────────────
st.subheader("📉 Overall Trend Analysis")

trend = report.overall_trend

t1, t2, t3, t4 = st.columns(4)
with t1:
    direction_class = {
        "improving": "trend-down", "worsening": "trend-up",
        "stable": "trend-flat", "volatile": "trend-flat",
    }.get(trend.direction.value, "trend-flat")
    st.markdown(f"Direction: **{trend.direction.value.title()}**")
with t2:
    delta_color = "normal" if trend.slope_per_year < 0 else "inverse"
    st.metric("Change/Year", f"{trend.slope_per_year:+,.0f} kg", delta_color=delta_color)
with t3:
    st.metric("R² Confidence", f"{trend.r_squared:.2f}")
with t4:
    st.metric("Monthly Change", f"{trend.pct_change_monthly:+.2f}%")

st.info(f"💡 {trend.interpretation}")

# ─── Footprint Timeline ─────────────────────────────────────────────────────
st.subheader("📅 Footprint Timeline")

if report.footprint_timeline:
    df_tl = pd.DataFrame(report.footprint_timeline)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df_tl["date"], y=df_tl["footprint"],
            mode="lines+markers", name="Footprint (kg CO₂)",
            line=dict(color="#ef4444", width=2),
            marker=dict(size=6),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df_tl["date"], y=df_tl["eco_score"],
            mode="lines+markers", name="Eco Score",
            line=dict(color="#22c55e", width=2, dash="dot"),
            marker=dict(size=5),
        ),
        secondary_y=True,
    )

    # Add trend line
    if len(df_tl) > 1:
        x_idx = list(range(len(df_tl)))
        slope = trend.slope_per_month
        intercept = trend.intercept
        trend_line = [slope * xi + intercept for xi in x_idx]
        fig.add_trace(
            go.Scatter(
                x=df_tl["date"], y=trend_line,
                mode="lines", name="Trend Line",
                line=dict(color="#6b7280", width=2, dash="dash"),
            ),
            secondary_y=False,
        )

    fig.update_layout(
        title="Footprint & Eco Score Over Time",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Footprint (kg CO₂)", secondary_y=False)
    fig.update_yaxes(title_text="Eco Score", secondary_y=True, range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# ─── Category Trends ────────────────────────────────────────────────────────
if report.category_trends:
    st.subheader("🏷️ Category Trends")

    df_cat = pd.DataFrame([ct.to_dict() for ct in report.category_trends])

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        fig_cat = px.bar(
            df_cat, x="category", y="change_pct",
            color="direction",
            color_discrete_map={
                "improving": "#22c55e", "worsening": "#ef4444",
                "stable": "#6b7280", "volatile": "#f59e0b",
            },
            title="Category Emission Change (%)",
            labels={"change_pct": "Change %", "category": "Category"},
        )
        fig_cat.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_table:
        st.dataframe(
            df_cat[["category", "current_avg", "previous_avg", "change_pct", "direction", "contribution_to_total"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "current_avg": st.column_config.NumberColumn("Current Avg", format="%.0f kg"),
                "previous_avg": st.column_config.NumberColumn("Previous Avg", format="%.0f kg"),
                "change_pct": st.column_config.NumberColumn("Change %", format="%+.1f%%"),
                "contribution_to_total": st.column_config.NumberColumn("Share %", format="%.1f%%"),
            },
        )

# ─── Seasonal Patterns ─────────────────────────────────────────────────────
if report.seasonal_patterns:
    st.subheader("🌡️ Seasonal Patterns")

    df_season = pd.DataFrame([sp.to_dict() for sp in report.seasonal_patterns])

    col_pie, col_bar = st.columns(2)

    with col_pie:
        fig_pie = px.pie(
            df_season, values="sample_count", names="season",
            title="Assessment Distribution by Season",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        fig_sbar = px.bar(
            df_season, x="season", y="avg_footprint",
            color="deviation_from_mean",
            color_continuous_scale=["#22c55e", "#ef4444"],
            title="Average Footprint by Season",
        )
        fig_sbar.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_sbar, use_container_width=True)

# ─── Anomalies ──────────────────────────────────────────────────────────────
if report.anomalies:
    st.subheader(f"⚠️ Detected Anomalies ({len(report.anomalies)})")

    for anomaly in report.anomalies:
        icon = "🔴" if anomaly.is_spike else "🟢"
        hint = f" — likely **{anomaly.category_hint}**" if anomaly.category_hint else ""
        st.markdown(
            f'<div class="anomaly-card">'
            f'{icon} <strong>{anomaly.date}</strong> — '
            f'Footprint: <strong>{anomaly.footprint:,.0f} kg</strong> '
            f'(expected: {anomaly.expected_value:,.0f} kg, '
            f'deviation: {anomaly.deviation:+,.0f} kg / {anomaly.deviation_pct:+.1f}%){hint}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ─── Forecasts ──────────────────────────────────────────────────────────────
if report.forecasts:
    st.subheader("🔮 Emission Forecasts")

    df_fc = pd.DataFrame([f.to_dict() for f in report.forecasts])

    scenarios = df_fc["scenario"].unique()
    fig_fc = go.Figure()

    colors = {"current_trend": "#3b82f6", "optimistic": "#22c55e", "pessimistic": "#ef4444"}
    labels = {"current_trend": "Current Trend", "optimistic": "Optimistic (-5%/mo)", "pessimistic": "Pessimistic (+3%/mo)"}

    for scenario in scenarios:
        df_s = df_fc[df_fc["scenario"] == scenario]
        fig_fc.add_trace(go.Scatter(
            x=df_s["date_label"], y=df_s["predicted_footprint"],
            mode="lines+markers", name=labels.get(scenario, scenario),
            line=dict(color=colors.get(scenario, "#6b7280"), width=2),
        ))
        # Confidence band for current trend only
        if scenario == "current_trend":
            fig_fc.add_trace(go.Scatter(
                x=list(df_s["date_label"]) + list(df_s["date_label"][::-1]),
                y=list(df_s["confidence_upper"]) + list(df_s["confidence_lower"][::-1]),
                fill="toself", fillcolor="rgba(59,130,246,0.1)",
                line=dict(width=0), showlegend=False, name="95% CI",
            ))

    # Goal line
    if report.goal_target:
        fig_fc.add_hline(
            y=report.goal_target, line_dash="dot", line_color="#22c55e",
            annotation_text=f"Goal: {report.goal_target:,.0f} kg",
        )

    fig_fc.update_layout(
        title=f"Footprint Forecast — Next {forecast_months} Months",
        yaxis_title="Predicted Footprint (kg CO₂)",
        height=450, hovermode="x unified",
    )
    st.plotly_chart(fig_fc, use_container_width=True)

# ─── Insights ───────────────────────────────────────────────────────────────
if report.insights:
    st.subheader("💡 Personalised Insights")

    severity_css = {
        "critical": "insight-critical",
        "warning": "insight-warning",
        "info": "insight-info",
        "positive": "insight-positive",
    }
    severity_icons = {
        "critical": "🚨", "warning": "⚠️", "info": "ℹ️", "positive": "✅",
    }

    for insight in report.insights:
        css_class = severity_css.get(insight.severity.value, "insight-info")
        icon = severity_icons.get(insight.severity.value, "💡")
        st.markdown(
            f'<div class="{css_class}">'
            f'{icon} <strong>{insight.title}</strong><br/>'
            f'{insight.description}<br/>'
            f'<em>Recommended: {insight.action}</em>'
            f'{" — Potential saving: " + f"{insight.potential_saving_kg:,.0f} kg CO₂" if insight.potential_saving_kg > 0 else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ─── Distribution Chart ─────────────────────────────────────────────────────
if report.footprint_timeline:
    st.subheader("📊 Footprint Distribution")

    df_dist = pd.DataFrame(report.footprint_timeline)
    fig_dist = px.histogram(
        df_dist, x="footprint", nbins=15,
        title="Footprint Distribution",
        labels={"footprint": "Footprint (kg CO₂)"},
        color_discrete_sequence=["#3b82f6"],
    )
    fig_dist.add_vline(x=report.avg_footprint, line_dash="dash", line_color="#ef4444",
                       annotation_text=f"Avg: {report.avg_footprint:,.0f}")
    fig_dist.add_vline(x=report.median_footprint, line_dash="dash", line_color="#22c55e",
                       annotation_text=f"Median: {report.median_footprint:,.0f}")
    fig_dist.update_layout(height=350)
    st.plotly_chart(fig_dist, use_container_width=True)

# ─── Eco Score Timeline ─────────────────────────────────────────────────────
if report.eco_score_timeline:
    st.subheader("⭐ Eco Score Trajectory")

    df_es = pd.DataFrame(report.eco_score_timeline)
    fig_es = px.line(
        df_es, x="date", y="eco_score",
        title="Eco Score Over Time",
        markers=True,
        color_discrete_sequence=["#22c55e"],
    )
    fig_es.add_hline(y=75, line_dash="dot", line_color="#f59e0b",
                     annotation_text="Target: 75")
    fig_es.update_layout(height=350, yaxis_range=[0, 105])
    st.plotly_chart(fig_es, use_container_width=True)

# ─── Raw Data ───────────────────────────────────────────────────────────────
with st.expander("📋 Raw Analysis Data (JSON)", expanded=False):
    st.json(report.to_dict())

# ─── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
    f"Analysed {report.total_assessments} assessments over {report.analysis_period_months} months"
)
