"""
Commute Cost Calculator — Streamlit Page

Compare financial, environmental, and time costs across 14 transport modes
with interactive visualisations, savings projections, and breakeven analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from src.lifestyle.commute_cost_calculator import (
    TransportMode,
    WeatherCondition,
    TrafficLevel,
    VehicleInfo,
    CommuteProfile,
    CostBreakdown,
    EnvironmentalImpact,
    TimeMetrics,
    ModeComparison,
    MODE_LABELS,
    ACTIVE_MODES,
    calculate_single_mode,
    calculate_commute_comparison,
    calculate_savings_vs_driving,
    calculate_breakeven_analysis,
    generate_commute_report,
    format_currency,
    format_co2,
    format_time,
)

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Commute Cost Calculator",
    page_icon="💰",
    layout="wide",
)

st.markdown("""
<style>
    .cost-card {
        background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .cost-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }
    .cost-card h3 { margin: 0 0 8px; }
    .metric-row { display: flex; gap: 16px; flex-wrap: wrap; }
    .metric-pill {
        background: #ffffff; border: 1px solid #e5e7eb;
        border-radius: 8px; padding: 8px 14px; font-size: 13px;
    }
    .winner-badge {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: #fff; border-radius: 20px; padding: 4px 12px;
        font-weight: 700; font-size: 12px;
    }
    .warning-pill {
        background: #fef3c7; border: 1px solid #fbbf24;
        border-radius: 6px; padding: 4px 10px; font-size: 12px;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar Inputs ─────────────────────────────────────────────────────────
st.sidebar.header("🔧 Commute Settings")

distance = st.sidebar.slider(
    "One-way distance (km)", 0.5, 100.0, 15.0, 0.5,
    help="Distance from home to work/school.",
)
work_days = st.sidebar.slider("Work days per week", 1, 7, 5)
weeks_per_year = st.sidebar.slider("Working weeks per year", 20, 52, 48)
hourly_wage = st.sidebar.number_input(
    "Your hourly wage (USD)", 0.0, 500.0, 25.0, 5.0,
    help="Used to calculate time-cost of commuting.",
)

weather_label = st.sidebar.selectbox(
    "Typical weather", [w.value.replace("_", " ").title() for w in WeatherCondition],
)
traffic_label = st.sidebar.selectbox(
    "Typical traffic", [t.value.title() for t in TrafficLevel],
)
region = st.sidebar.selectbox("Region (fuel prices)", ["US", "EU", "UK", "India", "Global"])

weather = WeatherCondition(weather_label.lower().replace(" ", "_"))
traffic = TrafficLevel(traffic_label.lower())

# Vehicle details (collapsed)
with st.sidebar.expander("🚗 Vehicle details (if applicable)", expanded=False):
    mpg = st.number_input("Fuel efficiency (MPG)", 10.0, 80.0, 28.0, 1.0)
    insurance = st.number_input("Annual insurance (USD)", 0.0, 10000.0, 1800.0, 100.0)
    depreciation = st.number_input("Annual depreciation (USD)", 0.0, 20000.0, 3000.0, 500.0)
    parking = st.number_input("Daily parking cost (USD)", 0.0, 50.0, 0.0, 1.0)
    tolls = st.number_input("Tolls per trip (USD)", 0.0, 20.0, 0.0, 0.50)

with st.sidebar.expander("⛽ Fuel & Fare Details", expanded=False):
    fuel_type = st.selectbox("Fuel type", ["gasoline", "diesel", "hybrid", "electric"])

vehicle = VehicleInfo(
    fuel_efficiency_mpg=mpg,
    annual_insurance_usd=insurance,
    annual_depreciation_usd=depreciation,
    monthly_parking_usd=parking * 30,
)

profile = CommuteProfile(
    distance_km=distance,
    work_days_per_week=work_days,
    weeks_per_year=weeks_per_year,
    vehicle=vehicle,
    weather=weather,
    traffic=traffic,
    parking_cost_per_day=parking,
    toll_cost_per_trip=tolls,
    hourly_wage_usd=hourly_wage,
    region=region,
)


# ─── Main Content ───────────────────────────────────────────────────────────
st.title("💰 Commute Cost Calculator")
st.markdown(
    "Compare **financial costs**, **CO₂ emissions**, and **time investment** "
    "across **14 transport modes** — with annual projections and savings analysis."
)

# Run calculations
report = generate_commute_report(profile)
comparisons = [ModeComparison(**c) if isinstance(c, dict) else c for c in report["comparisons"]]
if comparisons and isinstance(comparisons[0], dict):
    comparisons = []
    for c_dict in report["comparisons"]:
        cb_dict = c_dict["cost_breakdown"]
        env_dict = c_dict["environmental"]
        tm_dict = c_dict["time_metrics"]
        cb = CostBreakdown(**{k: v for k, v in cb_dict.items()
                              if k in CostBreakdown.__dataclass_fields__})
        env = EnvironmentalImpact(**{k: v for k, v in env_dict.items()
                                     if k in EnvironmentalImpact.__dataclass_fields__})
        tm = TimeMetrics(**{k: v for k, v in tm_dict.items()
                            if k in TimeMetrics.__dataclass_fields__})
        comparisons.append(ModeComparison(
            mode=c_dict["mode"], mode_label=c_dict["mode_label"],
            cost_breakdown=cb, environmental=env, time_metrics=tm,
            annual_financial_cost=c_dict["annual_financial_cost"],
            annual_total_cost=c_dict["annual_total_cost"],
            annual_co2_kg=c_dict["annual_co2_kg"],
            score=c_dict["score"],
            recommendation_tag=c_dict["recommendation_tag"],
            warnings=c_dict.get("warnings", []),
        ))

summary = report["summary"]

# ─── Top Metrics Row ────────────────────────────────────────────────────────
st.subheader("📊 Quick Summary")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Best Mode", summary["best_mode"])
with col2:
    st.metric("Best Score", f"{summary['best_score']}/100")
with col3:
    st.metric(
        "Potential Annual Savings",
        format_currency(summary["potential_annual_savings_usd"]),
    )
with col4:
    st.metric(
        "CO₂ Reduction",
        format_co2(summary["potential_annual_co2_reduction_kg"]),
    )

st.caption(
    f"📅 Based on {report['profile']['annual_trips']} round trips/year "
    f"({work_days} days × {weeks_per_year} weeks × 2)"
)

# ─── Score Comparison Chart ─────────────────────────────────────────────────
st.subheader("🏆 Mode Rankings")

df_scores = pd.DataFrame([
    {
        "Mode": c.mode_label,
        "Score": c.score,
        "Annual Cost ($)": c.annual_financial_cost,
        "CO₂ (kg/yr)": c.annual_co2_kg,
        "Travel Time (min)": c.time_metrics.travel_time_minutes,
    }
    for c in comparisons
])

fig_scores = px.bar(
    df_scores, x="Score", y="Mode", orientation="h",
    color="Score",
    color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
    range_color=[0, 100],
    title="Commute Mode Score (higher = better)",
)
fig_scores.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=500,
    showlegend=False,
)
st.plotly_chart(fig_scores, use_container_width=True)

# ─── Cost vs CO₂ Scatter ────────────────────────────────────────────────────
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_scatter = px.scatter(
        df_scores, x="Annual Cost ($)", y="CO₂ (kg/yr)",
        size="Travel Time (min)", color="Mode",
        title="Annual Cost vs CO₂ Emissions",
        hover_data=["Score"],
        size_max=30,
    )
    fig_scatter.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_chart2:
    fig_time = px.bar(
        df_scores, x="Mode", y="Travel Time (min)",
        color="Mode",
        title="One-way Travel Time by Mode",
    )
    fig_time.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_time, use_container_width=True)

# ─── Detailed Cost Breakdown Table ──────────────────────────────────────────
st.subheader("💳 Detailed Cost Breakdown (per trip)")

breakdown_rows = []
for c in comparisons:
    breakdown_rows.append({
        "Mode": c.mode_label,
        "Score": c.score,
        "Fuel/Fare": format_currency(c.cost_breakdown.fuel_cost + c.cost_breakdown.fare_cost),
        "Maintenance": format_currency(c.cost_breakdown.maintenance_cost),
        "Insurance": format_currency(c.cost_breakdown.insurance_daily),
        "Parking": format_currency(c.cost_breakdown.parking_cost),
        "Depreciation": format_currency(c.cost_breakdown.depreciation_daily),
        "Wear & Tear": format_currency(c.cost_breakdown.wear_tear_cost),
        "Time Cost": format_currency(c.cost_breakdown.time_cost),
        "Health Benefit": f"-{format_currency(c.cost_breakdown.health_benefit)}" if c.cost_breakdown.health_benefit > 0 else "$0.00",
        "Total/Trip": format_currency(c.cost_breakdown.total_financial),
    })

st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)

# ─── Environmental Impact ───────────────────────────────────────────────────
st.subheader("🌍 Environmental Impact")

env_rows = []
for c in comparisons:
    env_rows.append({
        "Mode": c.mode_label,
        "CO₂/trip (kg)": c.environmental.co2_kg,
        "NOx/trip (g)": c.environmental.nox_grams,
        "PM2.5/trip (g)": c.environmental.pm25_grams,
        "Annual CO₂ (kg)": c.environmental.co2_annual_kg,
        "Trees Needed": c.environmental.trees_needed,
        "Car Days Equiv.": c.environmental.equivalence_car_days,
    })

df_env = pd.DataFrame(env_rows)

fig_co2 = px.bar(
    df_env, x="Mode", y="Annual CO₂ (kg)",
    color="Annual CO₂ (kg)",
    color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
    title="Annual CO₂ Emissions by Mode",
)
fig_co2.update_layout(height=350, xaxis_tickangle=-45, showlegend=False)
st.plotly_chart(fig_co2, use_container_width=True)

st.dataframe(df_env, use_container_width=True, hide_index=True)

# ─── Detailed Mode Cards ────────────────────────────────────────────────────
st.subheader("📋 Detailed Mode Analysis")

for i, c in enumerate(comparisons):
    is_top = i == 0
    with st.expander(
        f"{'🏆 ' if is_top else ''}{c.mode_label} — Score: {c.score}/100 "
        f"| {format_currency(c.annual_financial_cost)}/yr | {format_co2(c.annual_co2_kg)}/yr",
        expanded=is_top,
    ):
        # Recommendation badge
        st.markdown(f"**{c.recommendation_tag}**")

        # Warnings
        if c.warnings:
            for w in c.warnings:
                st.markdown(f'<span class="warning-pill">{w}</span>', unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Per Trip Cost", format_currency(c.cost_breakdown.total_financial))
        with m2:
            st.metric("CO₂ per Trip", format_co2(c.environmental.co2_kg))
        with m3:
            st.metric("Travel Time", format_time(c.time_metrics.travel_time_minutes))
        with m4:
            st.metric("Health Benefit", format_currency(c.cost_breakdown.health_benefit))

        # Cost pie chart
        cost_data = {
            "Fuel/Fare": c.cost_breakdown.fuel_cost + c.cost_breakdown.fare_cost,
            "Maintenance": c.cost_breakdown.maintenance_cost,
            "Insurance": c.cost_breakdown.insurance_daily,
            "Parking": c.cost_breakdown.parking_cost,
            "Depreciation": c.cost_breakdown.depreciation_daily,
            "Wear & Tear": c.cost_breakdown.wear_tear_cost,
            "Time": c.cost_breakdown.time_cost,
        }
        cost_data = {k: v for k, v in cost_data.items() if v > 0}
        if cost_data:
            fig_pie = px.pie(
                names=list(cost_data.keys()), values=list(cost_data.values()),
                title="Cost Distribution per Trip",
                hole=0.4,
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Annual projection
        st.markdown(f"**Annual Projection:** {report['profile']['annual_trips']} round trips")
        a1, a2, a3 = st.columns(3)
        with a1:
            st.metric("Annual Financial Cost", format_currency(c.annual_financial_cost))
        with a2:
            st.metric("Annual CO₂", format_co2(c.annual_co2_kg))
        with a3:
            st.metric("Annual Time", format_time(c.time_metrics.travel_time_annual_hours * 60))


# ─── Savings vs Driving ─────────────────────────────────────────────────────
st.subheader("💰 Savings Analysis vs Driving (Gasoline)")

savings_data = []
for c in comparisons:
    if c.mode != "driving_gas":
        savings = calculate_savings_vs_driving(profile, c.mode)
        savings_data.append({
            "Mode": c.mode_label,
            "Financial Saved/yr": savings["annual_financial_saved_usd"],
            "CO₂ Saved/yr (kg)": savings["annual_co2_saved_kg"],
            "Trees Equiv.": savings["trees_equivalent"],
            "Cost Reduction %": savings["percent_cost_reduction"],
        })

if savings_data:
    df_savings = pd.DataFrame(savings_data).sort_values("Financial Saved/yr", ascending=False)
    st.dataframe(df_savings, use_container_width=True, hide_index=True)

    fig_savings = px.bar(
        df_savings, x="Mode", y="Financial Saved/yr",
        color="Financial Saved/yr",
        color_continuous_scale=["#fbbf2b", "#22c55e"],
        title="Annual Financial Savings vs Driving Gasoline",
    )
    fig_savings.update_layout(height=350, xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_savings, use_container_width=True)


# ─── Breakeven Analysis ─────────────────────────────────────────────────────
st.subheader("📈 Breakeven Analysis")
st.markdown("How long does it take for a new transport investment to pay for itself?")

breakeven_investments = [
    ("ebike", 1500, "E-Bike"),
    ("driving_ev", 5000, "EV Upgrade Premium"),
    ("ebike", 3000, "Premium E-Bike"),
    ("scooter", 800, "Electric Scooter"),
]

be_data = []
for target_mode, inv_usd, inv_name in breakeven_investments:
    result = calculate_breakeven_analysis(profile, target_mode, inv_usd, inv_name)
    be_data.append({
        "Investment": inv_name,
        "Cost": format_currency(inv_usd),
        "Target Mode": result["target_mode"],
        "Daily Saving": format_currency(result["daily_saving_usd"]),
        "Days to Breakeven": result["days_to_breakeven"],
        "Years": result["years_to_breakeven"],
        "5-Year Net Benefit": format_currency(result["five_year_net_benefit"]),
    })

if be_data:
    st.dataframe(pd.DataFrame(be_data), use_container_width=True, hide_index=True)

# ─── Combined Cost + CO₂ Radar ──────────────────────────────────────────────
st.subheader("🕸️ Multi-Dimensional Comparison")

# Normalize scores for radar chart
top_modes = comparisons[:8]
categories = ["Financial", "Environmental", "Time", "Health", "Overall"]

fig_radar = go.Figure()
for c in top_modes:
    cost_norm = max(0, 100 - (c.annual_financial_cost / max(comp.annual_financial_cost for comp in comparisons) * 100)) if max(comp.annual_financial_cost for comp in comparisons) > 0 else 50
    env_norm = max(0, 100 - (c.annual_co2_kg / max(comp.annual_co2_kg for comp in comparisons) * 100)) if max(comp.annual_co2_kg for comp in comparisons) > 0 else 100
    time_norm = max(0, 100 - (c.time_metrics.travel_time_minutes / 60 * 100))
    health_norm = min(100, c.time_metrics.health_minutes_gained / 30 * 100) if c.time_metrics.health_minutes_gained > 0 else 10

    fig_radar.add_trace(go.Scatterpolar(
        r=[cost_norm, env_norm, time_norm, health_norm, c.score],
        theta=categories + [categories[0]],
        fill="toself",
        name=c.mode_label,
    ))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    height=500,
    title="Multi-Dimensional Mode Comparison",
)
st.plotly_chart(fig_radar, use_container_width=True)


# ─── Monthly Projection Chart ───────────────────────────────────────────────
st.subheader("📅 Monthly Cost Projection")

best = comparisons[0] if comparisons else None
worst = next((c for c in comparisons if c.mode == "driving_gas"), comparisons[-1] if comparisons else None)

if best and worst:
    months = pd.date_range(start=datetime.now(), periods=12, freq="MS")
    best_monthly = best.annual_financial_cost / 12
    worst_monthly = worst.annual_financial_cost / 12

    monthly_df = pd.DataFrame({
        "Month": [m.strftime("%b") for m in months],
        f"Best ({best.mode_label})": [round(best_monthly * (i + 1), 2) for i in range(12)],
        f"Worst ({worst.mode_label})": [round(worst_monthly * (i + 1), 2) for i in range(12)],
    })

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Scatter(
        x=monthly_df["Month"], y=monthly_df[f"Best ({best.mode_label})"],
        mode="lines+markers", name=f"Best: {best.mode_label}",
        line=dict(color="#22c55e", width=3),
    ))
    fig_monthly.add_trace(go.Scatter(
        x=monthly_df["Month"], y=monthly_df[f"Worst ({worst.mode_label})"],
        mode="lines+markers", name=f"Worst: {worst.mode_label}",
        line=dict(color="#ef4444", width=3),
    ))
    fig_monthly.update_layout(
        title="Cumulative Annual Cost Projection",
        yaxis_title="Cumulative Cost (USD)",
        height=400,
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

# ─── Footnote ───────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "💡 Costs are estimates based on averages for your region. "
    "Actual costs vary by specific vehicle, route, driving style, and local prices. "
    "Environmental factors use standard emission models."
)
st.caption(f"Generated: {report['generated_at'][:19]} | Modes compared: {summary['modes_compared']}")
