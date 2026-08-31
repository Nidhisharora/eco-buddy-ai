"""
Carbon Offset Portfolio Tracker — Streamlit Page
=================================================

Full-featured UI for managing, analysing, and projecting a user's
carbon offset portfolio.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime

from src.lib.carbon_offset_portfolio import (
    OFFSET_PROJECTS,
    init_offset_portfolio_db,
    add_offset_purchase,
    get_user_holdings,
    delete_offset_holding,
    clear_user_holdings,
    compute_portfolio_summary,
    project_net_zero,
    save_portfolio_snapshot,
    get_portfolio_snapshots,
)


def _get_user_id() -> int:
    return st.session_state.get("user_id", 1)


def render_offset_portfolio_tracker() -> None:
    """Main render entry point for the Offset Portfolio Tracker page."""
    st.markdown(
        "<div class='section-header'>🌍 Carbon Offset Portfolio Tracker</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Track your offset investments, analyse portfolio diversity, "
        "assess risk, and project your path to carbon neutrality."
    )

    init_offset_portfolio_db()
    user_id = _get_user_id()

    tab_add, tab_portfolio, tab_project, tab_history = st.tabs([
        "➕ Add Offsets",
        "📊 Portfolio Analysis",
        "🔮 Net-Zero Projection",
        "📜 History",
    ])

    # ------------------------------------------------------------------
    # TAB 1 — Add Offset Purchase
    # ------------------------------------------------------------------
    with tab_add:
        st.subheader("Purchase Carbon Offsets")

        project_options = {
            pid: f"{p['name']} — ${p['price_per_tonne']:.0f}/tonne ({p['verification']})"
            for pid, p in OFFSET_PROJECTS.items()
        }
        selected = st.selectbox(
            "Offset Project",
            list(project_options.keys()),
            format_func=lambda k: project_options[k],
            key="offset_project_select",
        )

        project = OFFSET_PROJECTS[selected]
        col1, col2 = st.columns(2)
        with col1:
            tonnes = st.number_input(
                "Tonnes of CO₂",
                min_value=0.1,
                max_value=10000.0,
                value=1.0,
                step=0.5,
                key="offset_tonnes",
            )
        with col2:
            default_cost = round(tonnes * project["price_per_tonne"], 2)
            cost = st.number_input(
                "Cost (USD)",
                min_value=0.0,
                value=default_cost,
                step=1.0,
                key="offset_cost",
            )

        st.markdown(
            f"**Project:** {project['name']}  \n"
            f"**Region:** {project['region']}  \n"
            f"**Category:** {project['category'].replace('_', ' ').title()}  \n"
            f"**Verification:** {project['verification']}  \n"
            f"**Co-benefits:** {', '.join(project['co_benefits'])}  \n"
            f"**Rating:** {'⭐' * int(project['rating'])} ({project['rating']})"
        )

        notes = st.text_area("Notes (optional)", key="offset_notes", height=68)
        purchase_date = st.date_input(
            "Purchase Date",
            value=datetime.utcnow().date(),
            key="offset_date",
        )

        if st.button("➕ Add to Portfolio", use_container_width=True):
            holding_id = add_offset_purchase(
                user_id=user_id,
                project_id=selected,
                tonnes=tonnes,
                cost_usd=cost,
                purchase_date=purchase_date.isoformat(),
                notes=notes,
            )
            if holding_id:
                st.success(f"✅ Offset purchase recorded (ID: {holding_id})")
                st.rerun()
            else:
                st.error("Failed to record purchase. Check inputs.")

    # ------------------------------------------------------------------
    # TAB 2 — Portfolio Analysis
    # ------------------------------------------------------------------
    with tab_portfolio:
        st.subheader("Portfolio Overview")

        emissions = st.number_input(
            "Your annual carbon emissions (kg CO₂)",
            min_value=0.0,
            value=4000.0,
            step=100.0,
            key="annual_emissions_input",
        )

        summary = compute_portfolio_summary(user_id, annual_emissions_kg=emissions)

        if summary.holdings_count == 0:
            st.info("No offset holdings yet. Go to **Add Offsets** to get started!")
            return

        # Top-level metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Offsets", f"{summary.total_tonnes:.2f} t CO₂")
        m2.metric("Total Invested", f"${summary.total_cost_usd:,.2f}")
        m3.metric("Avg Cost/Tonne", f"${summary.avg_cost_per_tonne:.2f}")
        m4.metric("Diversification", f"{summary.diversification_score:.0f}/100")

        r1, r2, r3 = st.columns(3)
        r1.metric("Risk Rating", summary.risk_rating)
        r2.metric("Net-Zero Progress", f"{summary.net_zero_progress_pct:.1f}%")
        if summary.projected_neutral_date:
            r3.metric("Projected Neutral", summary.projected_neutral_date)
        else:
            r3.metric("Holdings", f"{summary.holdings_count}")

        # Category pie chart
        if summary.category_breakdown:
            st.markdown("### Category Breakdown")
            cats = list(summary.category_breakdown.keys())
            tonnes_vals = [summary.category_breakdown[c]["tonnes"] for c in cats]
            fig_pie = px.pie(
                names=[c.replace("_", " ").title() for c in cats],
                values=tonnes_vals,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_pie.update_traces(textinfo="label+percent")
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Regional bar chart
        if summary.regional_breakdown:
            st.markdown("### Regional Breakdown")
            fig_bar = px.bar(
                x=list(summary.regional_breakdown.keys()),
                y=list(summary.regional_breakdown.values()),
                labels={"x": "Region", "y": "Tonnes CO₂"},
                color=list(summary.regional_breakdown.keys()),
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_bar.update_layout(
                showlegend=False,
                margin=dict(t=20, b=20),
                height=280,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Holdings table
        st.markdown("### Holdings Detail")
        holdings = get_user_holdings(user_id)
        for h in holdings:
            proj = OFFSET_PROJECTS.get(h.project_id, {})
            with st.expander(
                f"{proj.get('name', h.project_id)} — {h.tonnes:.2f}t — ${h.cost_usd:.2f}"
            ):
                st.write(f"**Date:** {h.purchase_date}")
                st.write(f"**Verification:** {proj.get('verification', 'N/A')}")
                st.write(f"**Co-benefits:** {', '.join(proj.get('co_benefits', []))}")
                if h.notes:
                    st.write(f"**Notes:** {h.notes}")
                if st.button("🗑️ Remove", key=f"del_{h.id}"):
                    delete_offset_holding(user_id, h.id)
                    st.rerun()

        # Snapshot save
        if st.button("📸 Save Portfolio Snapshot", use_container_width=True):
            if save_portfolio_snapshot(user_id):
                st.success("Snapshot saved!")

    # ------------------------------------------------------------------
    # TAB 3 — Net-Zero Projection
    # ------------------------------------------------------------------
    with tab_project:
        st.subheader("Net-Zero Projection")

        proj_emissions = st.number_input(
            "Annual emissions (kg CO₂) for projection",
            min_value=0.0,
            value=4000.0,
            step=100.0,
            key="proj_emissions",
        )
        monthly_budget = st.number_input(
            "Monthly offset budget (USD)",
            min_value=0.0,
            value=50.0,
            step=5.0,
            key="proj_budget",
        )

        if st.button("🔮 Generate Projection", use_container_width=True):
            projection = project_net_zero(
                user_id,
                annual_emissions_kg=proj_emissions,
                monthly_offset_budget_usd=monthly_budget,
            )

            p1, p2, p3 = st.columns(3)
            p1.metric("Current Offsets", f"{projection.current_offset_tonnes:.2f} t")
            p2.metric("Annual Offset Rate", f"{projection.annual_offset_rate_tonnes:.2f} t/yr")
            if projection.years_to_neutral:
                p3.metric("Years to Neutral", f"{projection.years_to_neutral:.1f}")
            else:
                p3.metric("Years to Neutral", "—")

            if projection.monthly_offset_needed_tonnes > 0:
                st.metric(
                    "Monthly Offset Needed",
                    f"{projection.monthly_offset_needed_tonnes:.3f} tonnes",
                )
            if projection.cost_to_neutral_usd > 0:
                st.metric("Est. Cost to Neutral", f"${projection.cost_to_neutral_usd:,.2f}")

            # Timeline gauge
            if projection.neutral_date:
                fig_gauge = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=min(projection.current_offset_tonnes, proj_emissions / 1000),
                        number={"suffix": " t"},
                        delta={
                            "reference": 0,
                            "increasing": {"color": "#22c55e"},
                        },
                        title={"text": "Offset Progress (tonnes)"},
                        gauge={
                            "axis": {"range": [0, proj_emissions / 1000]},
                            "bar": {"color": "#22c55e"},
                            "steps": [
                                {"range": [0, proj_emissions / 2000], "color": "#f0fdf4"},
                                {"range": [proj_emissions / 2000, proj_emissions / 1000], "color": "#dcfce7"},
                            ],
                        },
                    )
                )
                fig_gauge.update_layout(height=280, margin=dict(t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            # Recommended actions
            if projection.recommended_actions:
                st.markdown("### 📋 Recommended Actions")
                for action in projection.recommended_actions:
                    st.markdown(f"- {action}")

    # ------------------------------------------------------------------
    # TAB 4 — Snapshot History
    # ------------------------------------------------------------------
    with tab_history:
        st.subheader("Portfolio Snapshot History")
        snapshots = get_portfolio_snapshots(user_id)
        if not snapshots:
            st.info("No snapshots saved yet. Analyse your portfolio and click Save Snapshot.")
        else:
            for snap in snapshots:
                with st.expander(f"📅 {snap['snapshot_date']} — {snap['total_tonnes']:.2f}t — ${snap['total_cost']:.2f}"):
                    st.write(f"**Diversification:** {snap['diversification_score']:.0f}/100")
                    st.write(f"**Risk Rating:** {snap['risk_rating']}")

            # Trend chart
            if len(snapshots) > 1:
                snap_dates = [s["snapshot_date"] for s in reversed(snapshots)]
                snap_tonnes = [s["total_tonnes"] for s in reversed(snapshots)]
                snap_costs = [s["total_cost"] for s in reversed(snapshots)]

                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=snap_dates, y=snap_tonnes,
                    name="Tonnes", line=dict(color="#22c55e", width=3),
                ))
                fig_trend.add_trace(go.Scatter(
                    x=snap_dates, y=snap_costs,
                    name="Cost ($)", line=dict(color="#3b82f6", width=3),
                    yaxis="y2",
                ))
                fig_trend.update_layout(
                    title="Portfolio Over Time",
                    yaxis=dict(title="Tonnes CO₂"),
                    yaxis2=dict(title="Cost ($)", overlaying="y", side="right"),
                    height=340,
                    margin=dict(t=40, b=20),
                )
                st.plotly_chart(fig_trend, use_container_width=True)

        if snapshots and st.button("🗑️ Clear All Snapshots", type="secondary"):
            st.warning("Snapshot clearing would require additional DB support.")


# Streamlit page entry
render_offset_portfolio_tracker()
