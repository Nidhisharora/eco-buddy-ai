"""
Page: Carbon Budget Planner
Set monthly carbon budgets, log daily spending, track category limits,
receive smart alerts, and visualize your carbon reduction journey.
"""

import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Carbon Budget Planner", page_icon="🎯", layout="wide")

from carbon_budget_service import (
    setup_budget, get_budget_summary, add_spending, quick_log,
    get_projection, get_category_suggestions, get_savings_tips,
)
from carbon_budget_cards import (
    inject_css, render_budget_overview_card, render_stat_grid,
    render_category_card, render_alert, render_suggestion_card,
    render_spending_log_form, render_budget_setup_form,
)
from carbon_budget_charts import (
    render_gauge_chart, render_category_bar_chart, render_daily_trend,
    render_projection_chart, render_history_line, render_pie_chart,
    render_co2_equivalence,
)
from carbon_budget_db import (
    seed_default_categories, ACTIVITY_CO2_DATABASE, get_unread_alerts,
    mark_alert_read, get_budget_history, get_spending_logs,
)

inject_css()

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("🔐 Please log in to use Carbon Budget Planner.")
    st.stop()

st.markdown("""
<div style="text-align:center;padding:20px 0 12px;background:linear-gradient(135deg,rgba(34,197,94,0.06),rgba(59,130,246,0.04));border-radius:16px;margin-bottom:20px;">
    <span style="font-size:36px;">🎯</span>
    <h1 style="margin:6px 0 2px;font-size:28px;font-weight:900;">Carbon Budget Planner</h1>
    <p style="color:#6b7280;font-size:14px;">Set limits, track spending, and stay on track with your carbon goals.</p>
</div>""", unsafe_allow_html=True)

categories = seed_default_categories()

# ── Setup or Summary ───────────────────────────────────────────────────
summary = get_budget_summary(user_id)

if not summary.get("has_budget"):
    st.info("No carbon budget set yet. Let's create one!")
    form = render_budget_setup_form()
    if form["submitted"]:
        setup_budget(user_id, form["monthly_limit_kg"])
        st.success("🎯 Carbon budget created!")
        st.rerun()
    st.stop()

# ── Alerts ─────────────────────────────────────────────────────────────
alerts = get_unread_alerts(user_id)
if alerts:
    with st.expander(f"🔔 {len(alerts)} New Alert(s)", expanded=True):
        for a in alerts:
            render_alert(a)
            if st.button("Dismiss", key=f"dismiss_{a['id']}"):
                mark_alert_read(a["id"])
                st.rerun()

# ── Overview ───────────────────────────────────────────────────────────
render_budget_overview_card(summary)
render_stat_grid({
    "daily_avg": f"{summary['daily_avg']} kg",
    "projected_month": f"{summary['projected_month']} kg",
    "daily_budget": f"{summary['daily_budget']} kg",
    "on_track": summary["on_track"],
})

# ── Equivalence ────────────────────────────────────────────────────────
if summary["monthly_spent"] > 0:
    saved = max(0, summary["monthly_limit"] - summary["monthly_spent"])
    if saved > 0:
        fig_eq = render_co2_equivalence(saved)
        st.plotly_chart(fig_eq, use_container_width=True)

# ── Main Tabs ──────────────────────────────────────────────────────────
st.markdown("---")
tab_log, tab_cats, tab_proj, tab_history, tab_tips = st.tabs([
    "📝 Log Spending", "📊 Categories", "📈 Projections", "📅 History", "💡 Tips"
])

# ── Log Spending ───────────────────────────────────────────────────────
with tab_log:
    form_data = render_spending_log_form(categories, ACTIVITY_CO2_DATABASE)
    if form_data["submitted"]:
        result = add_spending(user_id, form_data["category"], form_data["activity"],
                              form_data["co2_kg"], form_data["log_date"])
        if result["success"]:
            st.success(f"✅ Logged {form_data['co2_kg']:.1f} kg CO₂ for {form_data['activity']}")
            st.rerun()

    # Recent logs
    st.subheader("📋 Recent Spending")
    logs = get_spending_logs(user_id, limit=15)
    if logs:
        for log in logs:
            cat_label = categories.get(log["category"], {}).get("label", log["category"])
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-radius:10px;border:1px solid rgba(0,0,0,0.06);margin-bottom:6px;background:rgba(255,255,255,0.5);">
                <div>
                    <span style="font-weight:700;">{cat_label}</span>
                    <span style="color:#6b7280;font-size:13px;margin-left:8px;">{log['activity']}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:800;color:#ef4444;">{log['co2_kg']:.1f} kg</span>
                    <span style="font-size:11px;color:#9ca3af;margin-left:6px;">{log['log_date']}</span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.caption("No spending logged yet this month.")

# ── Categories ─────────────────────────────────────────────────────────
with tab_cats:
    st.subheader("📊 Category Breakdown")
    cat_status = summary.get("category_status", {})
    cat_labels = {k: v["label"] for k, v in categories.items()}
    for cat, status in cat_status.items():
        label = cat_labels.get(cat, cat)
        color = categories.get(cat, {}).get("color", "#22c55e")
        render_category_card(cat, label, status["spent"], status["limit"], color)

    # Charts
    col_pie, col_bar = st.columns(2)
    with col_pie:
        cat_data = summary.get("category_breakdown", {})
        if cat_data:
            fig_pie = render_pie_chart(cat_data, cat_labels)
            st.plotly_chart(fig_pie, use_container_width=True)
    with col_bar:
        cat_limits = summary.get("budget", {}).get("category_limits", {})
        cat_data = summary.get("category_breakdown", {})
        if cat_data:
            fig_bar = render_category_bar_chart(cat_data, cat_limits, cat_labels)
            st.plotly_chart(fig_bar, use_container_width=True)

# ── Projections ────────────────────────────────────────────────────────
with tab_proj:
    proj = get_projection(user_id)
    col_gauge, col_proj = st.columns(2)
    with col_gauge:
        fig_gauge = render_gauge_chart(summary["monthly_spent"], summary["monthly_limit"])
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col_proj:
        fig_proj = render_projection_chart(
            proj["projected_total"], proj["limit"], proj["daily_avg"], proj["days_remaining"])
        st.plotly_chart(fig_proj, use_container_width=True)

    if proj["will_exceed"]:
        st.warning(f"⚠️ At current rate, you'll exceed your budget by **{proj['projected_total'] - proj['limit']:.1f} kg**. "
                   f"Reduce daily spending by **{proj['daily_saving_needed']:.1f} kg/day** to stay on track.")
    else:
        st.success(f"✅ You're on track! Projected spend: **{proj['projected_total']:.1f} kg** "
                   f"(under your **{proj['limit']:.0f} kg** budget).")

    # Daily trend
    daily = summary.get("daily_history", [])
    if daily:
        fig_trend = render_daily_trend(daily, summary.get("daily_budget", 16.7))
        st.plotly_chart(fig_trend, use_container_width=True)

# ── History ────────────────────────────────────────────────────────────
with tab_history:
    st.subheader("📅 Monthly Budget History")
    history = get_budget_history(user_id)
    if history:
        fig_hist = render_history_line(history)
        st.plotly_chart(fig_hist, use_container_width=True)

        st.dataframe([
            {"Month": h["month"], "Spent (kg)": h["total_spent_kg"],
             "Limit (kg)": h["monthly_limit_kg"], "Saved (kg)": h["savings_kg"]}
            for h in history
        ], use_container_width=True)
    else:
        st.info("No history yet. Complete a month to see your budget history.")

# ── Tips ───────────────────────────────────────────────────────────────
with tab_tips:
    st.subheader("💡 Smart Suggestions")
    suggestions = get_category_suggestions(user_id)
    if suggestions:
        for s in suggestions:
            render_suggestion_card(s)
    else:
        st.success("🌟 Great job! You're within budget across all categories.")

    st.markdown("---")
    st.subheader("🌱 Savings Tips by Category")
    for cat, info in categories.items():
        with st.expander(f"{info['label']} Tips"):
            for tip in get_savings_tips(cat):
                st.markdown(f"- {tip}")

st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:14px;color:#9ca3af;font-size:13px;">
    🎯 Carbon Budget Planner — Track, limit, and reduce your carbon spending · Powered by EcoBuddy AI
</div>""", unsafe_allow_html=True)
Carbon Budget Planner Page
Set per-category carbon budgets, track usage, and get alerts
when limits are approached or exceeded.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from src.utils.carbon_budget_planner import (
    generate_budget_report, get_budget_template, calculate_category_budgets,
    DEFAULT_BUDGET_TEMPLATES,
)


def render_budget_gauge(score: dict) -> None:
    """Gauge showing overall budget score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score["score"],
        number={"suffix": "", "font": {"size": 36}},
        title={"text": f"Budget Score — Grade: {score['grade']}", "font": {"size": 16}},
        gauge={"axis": {"range": [0, 100]},
               "bar": {"color": "#22c55e" if score["score"] >= 75 else ("#f59e0b" if score["score"] >= 50 else "#ef4444")},
               "steps": [{"range": [0, 40], "color": "#fecaca"},
                         {"range": [40, 75], "color": "#fef3c7"},
                         {"range": [75, 100], "color": "#dcfce7"}]},
    ))
    fig.update_layout(height=280, margin=dict(t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_usage_bar_chart(evaluations: list[dict]) -> None:
    """Horizontal bar chart showing budget vs actual per category."""
    cats = [e["category"] for e in evaluations]
    budgets = [e["budget_kg"] for e in evaluations]
    actuals = [e["actual_kg"] for e in evaluations]
    colors = ["#ef4444" if a > b else "#22c55e" for a, b in zip(actuals, budgets)]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Budget", y=cats, x=budgets, orientation="h",
                         marker_color="#e5e7eb", text=[f"{b:.0f}" for b in budgets]))
    fig.add_trace(go.Bar(name="Actual", y=cats, x=actuals, orientation="h",
                         marker_color=colors, text=[f"{a:.0f}" for a in actuals]))
    fig.update_layout(barmode="overlay", height=280, margin=dict(t=20, b=20),
                      xaxis_title="kg CO₂/month", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)


def render_projection_chart(projections: dict, budgets: dict) -> None:
    """Bar chart comparing current vs projected month-end usage."""
    cats = list(projections.keys())
    current = [projections[c]["current_kg"] for c in cats]
    projected = [projections[c]["projected_month_end_kg"] for c in cats]
    budget_vals = [budgets.get(c, 0) for c in cats]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current", x=cats, y=current, marker_color="#3b82f6"))
    fig.add_trace(go.Bar(name="Projected (Month-End)", x=cats, y=projected,
                         marker_color="#f59e0b", marker_pattern_shape="//"))
    fig.add_trace(go.Scatter(name="Budget Limit", x=cats, y=budget_vals,
                             mode="lines+markers", line=dict(color="#ef4444", dash="dash", width=2)))
    fig.update_layout(barmode="group", height=300, margin=dict(t=30, b=30),
                      yaxis_title="kg CO₂", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)


def render_donut_breakdown(actuals: dict) -> None:
    """Donut chart of current actual usage by category."""
    cats = list(actuals.keys())
    vals = list(actuals.values())
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6"]

    fig = go.Figure(go.Pie(
        labels=cats, values=vals, hole=0.45,
        marker_colors=colors[:len(cats)],
        textinfo="label+percent",
    ))
    total = sum(vals)
    fig.update_layout(height=280, margin=dict(t=20, b=20),
                      annotations=[dict(text=f"{total:,.0f}<br>kg", x=0.5, y=0.5,
                                        font_size=16, showarrow=False)])
    st.plotly_chart(fig, use_container_width=True)


def render_alert_cards(alerts: list[dict]) -> None:
    """Render alert cards."""
    severity_styles = {
        "critical": ("#dc2626", "#fef2f2"),
        "high": ("#ea580c", "#fff7ed"),
        "medium": ("#ca8a04", "#fefce8"),
        "low": ("#2563eb", "#eff6ff"),
    }
    for alert in alerts:
        border_color, bg_color = severity_styles.get(alert["severity"], ("#6b7280", "#f9fafb"))
        st.markdown(
            f"<div style='padding:14px 18px; margin:10px 0; border-radius:12px; "
            f"border-left:5px solid {border_color}; background:{bg_color};'>"
            f"<strong>{alert['icon']} {alert['title']}</strong><br>"
            f"{alert['message']}<br>"
            f"<em style='color:#6b7280;'>💡 {alert['action']}</em>"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_budget_planner():
    """Main page render function."""
    st.markdown(
        "<div class='section-header'>💰 Carbon Budget Planner</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Set monthly carbon budgets per category, track your usage in real time, "
        "and get alerts before you overshoot."
    )

    # ── Budget Template Selection ───────────────────────────────────────
    st.subheader("🎯 Choose Budget Template")
    template_name = st.selectbox(
        "Budget Level",
        list(DEFAULT_BUDGET_TEMPLATES.keys()),
        format_func=lambda k: DEFAULT_BUDGET_TEMPLATES[k]["label"],
        index=1,
    )
    template = get_budget_template(template_name)
    st.caption(template["description"])

    # ── Custom Budget Override ──────────────────────────────────────────
    use_custom = st.checkbox("✏️ Customize budget amounts", value=False)

    if use_custom:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            b_t = st.number_input("Transport (kg/mo)", value=template["Transport"], step=10.0, key="b_t")
        with c2:
            b_e = st.number_input("Electricity (kg/mo)", value=template["Electricity"], step=10.0, key="b_e")
        with c3:
            b_d = st.number_input("Diet (kg/mo)", value=template["Diet"], step=10.0, key="b_d")
        with c4:
            b_f = st.number_input("Flights (kg/mo)", value=template["Flights"], step=10.0, key="b_f")
        budgets = {"Transport": b_t, "Electricity": b_e, "Diet": b_d, "Flights": b_f}
    else:
        budgets = {
            "Transport": template["Transport"],
            "Electricity": template["Electricity"],
            "Diet": template["Diet"],
            "Flights": template["Flights"],
        }

    st.markdown(f"**Total Monthly Budget:** {sum(budgets.values()):,.0f} kg CO₂")

    # ── Current Usage Inputs ────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Current Month Usage")

    day_of_month = st.slider("Day of month", 1, 31, datetime.now().day)

    a1, a2, a3, a4 = st.columns(4)
    with a1:
        a_t = st.number_input("Transport Used (kg)", min_value=0.0, value=140.0, step=5.0, key="a_t")
    with a2:
        a_e = st.number_input("Electricity Used (kg)", min_value=0.0, value=110.0, step=5.0, key="a_e")
    with a3:
        a_d = st.number_input("Diet Used (kg)", min_value=0.0, value=65.0, step=5.0, key="a_d")
    with a4:
        a_f = st.number_input("Flights Used (kg)", min_value=0.0, value=0.0, step=5.0, key="a_f")
    actuals = {"Transport": a_t, "Electricity": a_e, "Diet": a_d, "Flights": a_f}

    if st.button("📊 Generate Budget Report", use_container_width=True):
        report = generate_budget_report(budgets, actuals, day_of_month, template_name=template_name)

        # ── Score Overview ────────────────────────────────────────────
        st.divider()
        st.subheader("🎯 Budget Score")
        sc1, sc2 = st.columns([1, 2])
        with sc1:
            render_budget_gauge(report["score"])
        with sc2:
            score = report["score"]
            st.markdown(f"### Grade: {score['grade']} ({score['score']:.0f}/100)")
            st.markdown(score["description"])
            totals = report["totals"]
            st.metric("Total Used", f"{totals['actual_kg']:,.0f} kg",
                      delta=f"{totals['remaining_kg']:+,.0f} kg remaining",
                      delta_color="inverse" if totals["remaining_kg"] < 0 else "normal")

        # ── Budget vs Actual ──────────────────────────────────────────
        st.divider()
        st.subheader("📊 Budget vs Actual")
        render_usage_bar_chart(report["evaluations"])

        # Category detail table
        st.markdown("| Category | Budget | Actual | Remaining | Usage | Status |")
        st.markdown("|----------|--------|--------|-----------|-------|--------|")
        for ev in report["evaluations"]:
            st.markdown(
                f"| {ev['category']} | {ev['budget_kg']:,.0f} kg | "
                f"{ev['actual_kg']:,.0f} kg | {ev['remaining_kg']:+,.0f} kg | "
                f"{ev['usage_percent']:.0f}% | {ev['alert_icon']} |"
            )

        # ── Projections ───────────────────────────────────────────────
        st.divider()
        st.subheader("🔮 Month-End Projection")
        render_projection_chart(report["projections"], budgets)
        st.caption(
            f"Based on day {day_of_month} usage rate, projected month-end totals are shown "
            f"against budget limits (red dashed line)."
        )

        # ── Usage Breakdown ───────────────────────────────────────────
        sc1, sc2 = st.columns(2)
        with sc1:
            st.subheader("🥧 Usage Breakdown")
            render_donut_breakdown(actuals)
        with sc2:
            st.subheader("📋 Template Comparison")
            for t_name, t_data in DEFAULT_BUDGET_TEMPLATES.items():
                total = sum(t_data[c] for c in ["Transport", "Electricity", "Diet", "Flights"])
                active = " ← active" if t_name == template_name else ""
                st.markdown(f"**{t_data['label']}**{active}")
                st.caption(f"  {total:,.0f} kg/month total")

        # ── Alerts ────────────────────────────────────────────────────
        if report["alerts"]:
            st.divider()
            st.subheader("⚠️ Alerts")
            render_alert_cards(report["alerts"])
        else:
            st.divider()
            st.success("✅ No alerts — all categories are within budget!")

        # ── Recommendations ───────────────────────────────────────────
        st.divider()
        st.subheader("💡 Recommendations")
        for rec in report["recommendations"]:
            st.markdown(f"• {rec}")

    else:
        st.info("👆 Configure your budget and usage, then click **Generate Budget Report**.")


if __name__ == "__main__":
    st.set_page_config(page_title="Carbon Budget Planner — EcoBuddy AI", page_icon="💰", layout="wide")
    render_budget_planner()
else:
    render_budget_planner()
