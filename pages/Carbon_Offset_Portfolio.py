"""
Carbon Offset Portfolio Tracker — Streamlit Page

Interactive dashboard for managing and analyzing carbon offset investments.
Provides portfolio overview, project browsing, transaction logging,
lifecycle analysis, risk assessment, and impact reporting.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.portfolio.models import (
    OffsetProject,
    PortfolioHolding,
    OffsetTransaction,
    ProjectType,
    TransactionType,
    LifecycleStage,
    PortfolioSnapshot,
)
from src.portfolio.db import PortfolioDB
from src.portfolio.analytics import (
    PortfolioAnalyzer,
    calculate_diversification_score,
    calculate_portfolio_value,
    optimize_offset_allocation,
    compare_snapshots,
)
from src.portfolio.lifecycle import (
    LifecycleAnalyzer,
    calculate_permanence_score,
    compute_coeffectiveness_ratio,
    calculate_vintage_adjustment,
    compute_retirement_impact,
)

# ── Page Config ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Carbon Offset Portfolio — EcoBuddy AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Init ────────────────────────────────────────────────────

if "portfolio_db" not in st.session_state:
    st.session_state.portfolio_db = PortfolioDB()
if "user_id" not in st.session_state:
    st.session_state.user_id = 1  # Default user for demo

db: PortfolioDB = st.session_state.portfolio_db
user_id: int = st.session_state.user_id


# ── Helper functions ──────────────────────────────────────────────────────


def format_usd(value: float) -> str:
    """Format a value as US dollars."""
    return f"${value:,.2f}"


def format_kg(value: float) -> str:
    """Format kilograms with appropriate unit."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M kg"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}k kg"
    else:
        return f"{value:.0f} kg"


def risk_color(score: float) -> str:
    """Return a color string based on risk score."""
    if score < 30:
        return "🟢"
    elif score < 50:
        return "🟡"
    elif score < 70:
        return "🟠"
    else:
        return "🔴"


def lifecycle_emoji(stage: str) -> str:
    """Return an emoji for a lifecycle stage."""
    mapping = {
        "planning": "📋",
        "validation": "🔍",
        "registration": "📝",
        "verification": "✅",
        "active": "🟢",
        "serialization": "🏷️",
        "on_hold": "⏸️",
        "completed": "🏁",
        "expired": "⚠️",
        "revoked": "🚫",
    }
    return mapping.get(stage, "❓")


# ── Sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/earth-planet.png", width=64)
    st.title("🌍 Offset Portfolio")
    st.caption("Track · Analyze · Impact")

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard Overview",
            "🛒 Browse Projects",
            "💼 My Holdings",
            "📝 Transaction Log",
            "🔬 Lifecycle Analysis",
            "📈 Performance Trends",
            "🎯 Offset Optimizer",
            "⚙️ Settings",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Quick Stats**")

    holdings = db.get_user_holdings(user_id)
    total_invested = sum(h.total_invested_usd for h in holdings)
    total_offset_tonnes = sum(h.units_available for h in holdings)

    st.metric("💰 Total Invested", format_usd(total_invested))
    st.metric("🌱 Offsets Held", f"{total_offset_tonnes} tCO₂")
    st.metric("🏢 Projects", str(len(holdings)))


# ── Dashboard Overview ────────────────────────────────────────────────────

if page == "📊 Dashboard Overview":
    st.header("📊 Portfolio Dashboard")

    if not holdings:
        st.info(
            "Your offset portfolio is empty. Head to **Browse Projects** to "
            "start investing in verified carbon offset projects."
        )
    else:
        # Build analytics
        analyzer = PortfolioAnalyzer(holdings=holdings)
        snapshot = analyzer.generate_snapshot(user_id)
        impact = analyzer.get_impact_metrics()
        insights = analyzer.generate_insights()

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Portfolio Value",
                format_usd(snapshot.current_value_usd),
                delta=format_usd(snapshot.unrealized_gain_usd) if snapshot.unrealized_gain_usd else None,
            )
        with col2:
            st.metric(
                "Total Offset",
                format_kg(snapshot.total_carbon_offset_kg),
            )
        with col3:
            st.metric(
                "Diversification",
                f"{snapshot.diversification_score:.0f}/100",
            )
        with col4:
            st.metric(
                "Lifecycle Health",
                f"{snapshot.lifecycle_health:.0f}/100",
            )

        st.divider()

        # Charts row
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("Portfolio by Project Type")
            if snapshot.type_breakdown:
                type_df = pd.DataFrame(
                    list(snapshot.type_breakdown.items()),
                    columns=["Project Type", "Units"],
                )
                fig = px.pie(
                    type_df,
                    values="Units",
                    names="Project Type",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.4,
                )
                fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            st.subheader("Registry Breakdown")
            if snapshot.registry_breakdown:
                reg_df = pd.DataFrame(
                    list(snapshot.registry_breakdown.items()),
                    columns=["Registry", "Units"],
                )
                fig = px.bar(
                    reg_df,
                    x="Registry",
                    y="Units",
                    color="Registry",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Impact metrics
        st.subheader("🌍 Real-World Impact")
        imp_col1, imp_col2, imp_col3, imp_col4 = st.columns(4)
        with imp_col1:
            st.metric("🌳 Trees Equivalent", f"{impact['trees_equivalent']:.0f}")
        with imp_col2:
            st.metric("🚗 Cars Off Road", f"{impact['cars_off_road_days']:.0f} days")
        with imp_col3:
            st.metric("✈️ Flights Offset", f"{impact['flights_offset']:.0f}")
        with imp_col4:
            st.metric("💵 Cost/Tonne", format_usd(impact["effective_cost_per_tonne"]))

        # Insights
        if insights:
            st.subheader("💡 Insights")
            for insight in insights[:5]:
                with st.expander(f"{insight['icon']} {insight['title']}"):
                    st.write(insight["message"])


# ── Browse Projects ───────────────────────────────────────────────────────

elif page == "🛒 Browse Projects":
    st.header("🛒 Browse Offset Projects")

    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        type_filter = st.selectbox(
            "Project Type",
            ["All"] + [t.value.replace("_", " ").title() for t in ProjectType],
        )
    with filter_col2:
        registry_filter = st.selectbox(
            "Registry",
            ["All", "Verra", "Gold Standard", "ACR", "CAR", "Plan Vivo", "CDM"],
        )
    with filter_col3:
        country_filter = st.selectbox(
            "Country",
            ["All", "Brazil", "India", "Kenya", "Colombia", "Indonesia", "Peru", "Chile", "Costa Rica"],
        )

    # Query projects
    ptype = type_filter.lower().replace(" ", "_") if type_filter != "All" else None
    registry = registry_filter if registry_filter != "All" else None
    country = country_filter if country_filter != "All" else None

    projects = db.list_projects(
        project_type=ptype,
        registry=registry,
        country=country,
        limit=50,
    )

    if not projects:
        st.info(
            "No projects found matching your filters. "
            "Sample projects are loaded during database initialization."
        )

        # Offer to load sample projects
        if st.button("📦 Load Sample Projects", type="primary"):
            sample_projects = _get_sample_projects()
            for p in sample_projects:
                db.upsert_project(p)
            st.success(f"Loaded {len(sample_projects)} sample projects!")
            st.rerun()
    else:
        st.write(f"Showing **{len(projects)}** projects")

        for project in projects:
            with st.expander(
                f"{lifecycle_emoji(project.lifecycle_stage.value)} "
                f"**{project.name}** — {format_usd(project.unit_price_usd)}/unit"
            ):
                proj_col1, proj_col2 = st.columns([2, 1])

                with proj_col1:
                    st.write(f"**Type:** {project.project_type.value.replace('_', ' ').title()}")
                    st.write(f"**Registry:** {project.registry} | **Standard:** {project.standard}")
                    st.write(f"**Country:** {project.country} | **Vintage:** {project.vintage_year}")
                    st.write(f"**Available:** {project.available_units:,} units")
                    if project.description:
                        st.write(f"**Description:** {project.description}")
                    if project.co_benefits:
                        st.write(f"**Co-Benefits:** {', '.join(project.co_benefits)}")
                    if project.sdg_alignment:
                        st.write(f"**SDG Alignment:** {', '.join(str(s) for s in project.sdg_alignment)}")

                with proj_col2:
                    perm = calculate_permanence_score(project)
                    coeff = compute_coeffectiveness_ratio(project)
                    vintage_adj = calculate_vintage_adjustment(project.vintage_year)

                    st.metric("Permanence", f"{perm:.0f}/100")
                    st.metric("Co-effectiveness", f"{coeff:.2f}")
                    st.metric("Vintage Quality", f"{vintage_adj:.0%}")

                    units_to_buy = st.number_input(
                        "Units to purchase",
                        min_value=0,
                        max_value=project.available_units,
                        value=0,
                        key=f"buy_{project.project_id}",
                    )

                    if units_to_buy > 0:
                        total_cost = units_to_buy * project.unit_price_usd
                        st.write(f"**Total:** {format_usd(total_cost)}")

                        if st.button(
                            f"🛒 Purchase {units_to_buy} unit(s)",
                            key=f"purchase_{project.project_id}",
                        ):
                            # Create transaction
                            tx = OffsetTransaction(
                                user_id=user_id,
                                project_id=project.project_id,
                                project_name=project.name,
                                transaction_type=TransactionType.PURCHASE,
                                units=units_to_buy,
                                price_per_unit=project.unit_price_usd,
                                total_cost_usd=total_cost,
                                fee_usd=round(total_cost * 0.02, 2),  # 2% fee
                            )

                            # Create or update holding
                            existing_holdings = db.get_user_holdings(user_id)
                            existing = next(
                                (h for h in existing_holdings if h.project_id == project.project_id),
                                None,
                            )

                            if existing:
                                # Update existing holding with weighted average cost
                                total_units = existing.units_held + units_to_buy
                                weighted_cost = (
                                    (existing.avg_cost_per_unit * existing.units_held)
                                    + (project.unit_price_usd * units_to_buy)
                                ) / total_units
                                new_holding = PortfolioHolding(
                                    holding_id=existing.holding_id,
                                    user_id=user_id,
                                    project_id=project.project_id,
                                    project_name=project.name,
                                    project_type=project.project_type,
                                    units_held=total_units,
                                    units_retired=existing.units_retired,
                                    avg_cost_per_unit=round(weighted_cost, 4),
                                    total_invested_usd=existing.total_invested_usd + total_cost,
                                    purchase_date=existing.purchase_date,
                                    vintage_year=project.vintage_year,
                                    registry=project.registry,
                                )
                                db.update_holding_retirement(
                                    new_holding.holding_id, existing.units_retired
                                )
                            else:
                                new_holding = PortfolioHolding(
                                    user_id=user_id,
                                    project_id=project.project_id,
                                    project_name=project.name,
                                    project_type=project.project_type,
                                    units_held=units_to_buy,
                                    avg_cost_per_unit=project.unit_price_usd,
                                    total_invested_usd=total_cost,
                                    vintage_year=project.vintage_year,
                                    registry=project.registry,
                                )
                                db.add_holding(new_holding)

                            db.add_transaction(tx)
                            st.success(
                                f"✅ Purchased {units_to_buy} unit(s) from {project.name}!"
                            )
                            st.rerun()


def _get_sample_projects() -> List[OffsetProject]:
    """Generate sample offset projects for demonstration."""
    return [
        OffsetProject(
            project_id="proj-amazon-reforest",
            name="Amazon Reforestation Initiative",
            description="Large-scale reforestation in the Brazilian Amazon using native species, supporting indigenous communities.",
            project_type=ProjectType.REFORESTATION,
            registry="Verra",
            registry_id="VCS-2841",
            country="Brazil",
            region="Amazonas",
            latitude=-3.1,
            longitude=-60.0,
            methodology="VM0015",
            standard="VCS",
            vintage_year=2024,
            unit_price_usd=14.50,
            total_units=50000,
            available_units=42000,
            co_benefits=["Biodiversity protection", "Indigenous community support", "Water cycle restoration"],
            sdg_alignment=[13, 15, 1, 10],
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
        OffsetProject(
            project_id="proj-kerala-cookstoves",
            name="Clean Cookstoves — Kerala",
            description="Distributing efficient cookstoves to rural households in Kerala to reduce indoor air pollution and deforestation.",
            project_type=ProjectType.CLEAN_COOKSTOVES,
            registry="Gold Standard",
            registry_id="GS-1243",
            country="India",
            region="Kerala",
            latitude=10.85,
            longitude=76.27,
            methodology="GS-1 methodology",
            standard="Gold Standard",
            vintage_year=2025,
            unit_price_usd=8.20,
            total_units=100000,
            available_units=87000,
            co_benefits=["Improved health", "Gender equity", "Education support"],
            sdg_alignment=[3, 5, 4, 7, 13],
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
        OffsetProject(
            project_id="proj-kenya-solar",
            name="Kenya Solar Micro-Grid",
            description="Deploying solar micro-grids to off-grid communities in rural Kenya, replacing diesel generators.",
            project_type=ProjectType.RENEWABLE_ENERGY,
            registry="Verra",
            registry_id="VCS-3102",
            country="Kenya",
            region="Turkana",
            latitude=3.0,
            longitude=35.37,
            methodology="VM0010",
            standard="VCS",
            vintage_year=2024,
            unit_price_usd=11.80,
            total_units=75000,
            available_units=68000,
            co_benefits=["Energy access", "Economic development", "Health improvements"],
            sdg_alignment=[7, 8, 3, 13],
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
        OffsetProject(
            project_id="proj-colombia-red",
            name="Colombian REDD+ Forest Protection",
            description="Preventing deforestation in the Colombian Amazon through community-based forest monitoring.",
            project_type=ProjectType.REFORESTATION,
            registry="Verra",
            registry_id="VCS-1890",
            country="Colombia",
            region="Caquetá",
            latitude=1.0,
            longitude=-74.0,
            methodology="VM0015",
            standard="REDD+",
            vintage_year=2023,
            unit_price_usd=16.00,
            total_units=30000,
            available_units=24000,
            co_benefits=["Community livelihoods", "Biodiversity", "Water protection"],
            sdg_alignment=[13, 15, 1, 6],
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
        OffsetProject(
            project_id="proj-chile-wind",
            name="Patagonia Wind Farm",
            description="120MW wind farm in southern Chile displacing fossil fuel generation on the national grid.",
            project_type=ProjectType.RENEWABLE_ENERGY,
            registry="ACR",
            registry_id="ACR-456",
            country="Chile",
            region="Magallanes",
            latitude=-53.0,
            longitude=-70.0,
            methodology="ACM0002",
            standard="CDM",
            vintage_year=2024,
            unit_price_usd=9.50,
            total_units=80000,
            available_units=73000,
            co_benefits=["Grid decarbonization", "Rural employment"],
            sdg_alignment=[7, 8, 13],
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
        OffsetProject(
            project_id="proj-dac-iceland",
            name="Iceland Direct Air Capture",
            description="Geothermal-powered direct air capture facility in Iceland permanently sequestering CO₂ in basalt formations.",
            project_type=ProjectType.DIRECT_AIR_CAPTURE,
            registry="Verra",
            registry_id="VCS-4200",
            country="Iceland",
            region="Hellisheiði",
            latitude=64.04,
            longitude=-21.4,
            methodology="Novel DAC protocol",
            standard="VCS",
            vintage_year=2025,
            unit_price_usd=42.00,
            total_units=20000,
            available_units=18000,
            co_benefits=["Permanent storage", "Geothermal energy"],
            sdg_alignment=[7, 9, 13],
            lifecycle_stage=LifecycleStage.ACTIVE,
        ),
    ]


# ── My Holdings ───────────────────────────────────────────────────────────

elif page == "💼 My Holdings":
    st.header("💼 My Offset Holdings")

    holdings = db.get_user_holdings(user_id)

    if not holdings:
        st.info("No holdings yet. Browse projects to start your portfolio.")
    else:
        # Table view
        holdings_data = []
        for h in holdings:
            holdings_data.append({
                "Project": h.project_name,
                "Type": h.project_type.value.replace("_", " ").title(),
                "Registry": h.registry,
                "Units Held": h.units_held,
                "Units Retired": h.units_retired,
                "Available": h.units_available,
                "Avg Cost/Unit": format_usd(h.avg_cost_per_unit),
                "Total Cost": format_usd(h.total_invested_usd),
                "Vintage": h.vintage_year,
                "Purchased": h.purchase_date.strftime("%Y-%m-%d"),
            })

        st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)

        # Retirement section
        st.divider()
        st.subheader("🔄 Retire Offsets")

        st.write(
            "Retiring offsets permanently claims their environmental benefit. "
            "Retired offsets cannot be traded or resold."
        )

        retire_col1, retire_col2 = st.columns([3, 1])
        with retire_col1:
            retire_project = st.selectbox(
                "Select holding to retire from",
                [f"{h.project_name} ({h.units_available} available)" for h in holdings if h.units_available > 0],
            )
        with retire_col2:
            retire_units = st.number_input("Units to retire", min_value=1, value=1)

        if st.button("🔄 Retire Offsets", type="primary"):
            if retire_project:
                # Find the holding
                idx = next(
                    i for i, h in enumerate(holdings)
                    if f"{h.project_name} ({h.units_available} available)" == retire_project
                )
                holding = holdings[idx]

                if retire_units > holding.units_available:
                    st.error("Not enough available units to retire.")
                else:
                    new_retired = holding.units_retired + retire_units
                    db.update_holding_retirement(holding.holding_id, new_retired)

                    tx = OffsetTransaction(
                        user_id=user_id,
                        project_id=holding.project_id,
                        project_name=holding.project_name,
                        transaction_type=TransactionType.RETIREMENT,
                        units=retire_units,
                        price_per_unit=0.0,
                        total_cost_usd=0.0,
                    )
                    db.add_transaction(tx)

                    st.success(f"✅ Retired {retire_units} unit(s) from {holding.project_name}!")
                    st.balloons()
                    st.rerun()


# ── Transaction Log ───────────────────────────────────────────────────────

elif page == "📝 Transaction Log":
    st.header("📝 Transaction Log")

    tx_type_filter = st.selectbox(
        "Filter by type",
        ["All", "Purchase", "Retirement", "Transfer"],
    )
    tx_type = tx_type_filter.lower() if tx_type_filter != "All" else None

    transactions = db.get_user_transactions(user_id, tx_type=tx_type)

    if not transactions:
        st.info("No transactions recorded yet.")
    else:
        tx_data = []
        for tx in transactions:
            tx_data.append({
                "Date": tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                "Type": tx.transaction_type.value.title(),
                "Project": tx.project_name,
                "Units": tx.units,
                "Unit Price": format_usd(tx.price_per_unit),
                "Total": format_usd(tx.total_cost_usd),
                "Fee": format_usd(tx.fee_usd),
                "Status": tx.status.title(),
            })

        st.dataframe(pd.DataFrame(tx_data), use_container_width=True)

        # Monthly spend chart
        st.subheader("Monthly Spending")
        monthly: Dict[str, float] = {}
        for tx in transactions:
            if tx.transaction_type == TransactionType.PURCHASE:
                month_key = tx.timestamp.strftime("%Y-%m")
                monthly[month_key] = monthly.get(month_key, 0) + tx.total_cost_usd

        if monthly:
            spend_df = pd.DataFrame(
                list(monthly.items()), columns=["Month", "Amount ($)"]
            )
            fig = px.bar(spend_df, x="Month", y="Amount ($)", color_discrete_sequence=["#2ca02c"])
            fig.update_layout(margin=dict(t=20, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)


# ── Lifecycle Analysis ───────────────────────────────────────────────────

elif page == "🔬 Lifecycle Analysis":
    st.header("🔬 Lifecycle Analysis")

    if not holdings:
        st.info("Add offset holdings to view lifecycle analysis.")
    else:
        # Get projects for holdings
        projects_map: Dict[str, OffsetProject] = {}
        for h in holdings:
            project = db.get_project(h.project_id)
            if project:
                projects_map[h.project_id] = project

        analyzer = LifecycleAnalyzer()

        # Portfolio-level analysis
        st.subheader("📊 Portfolio Lifecycle Health")
        portfolio_analysis = analyzer.analyze_portfolio_lifecycle(holdings, projects_map)

        hl_col1, hl_col2, hl_col3, hl_col4 = st.columns(4)
        with hl_col1:
            grade = portfolio_analysis["health_grade"]
            st.metric("Health Grade", grade)
        with hl_col2:
            st.metric("Avg Permanence", f"{portfolio_analysis['avg_permanence']:.0f}/100")
        with hl_col3:
            st.metric("Avg Vintage Age", f"{portfolio_analysis['avg_vintage_age']:.1f} years")
        with hl_col4:
            st.metric("Lifecycle Score", f"{portfolio_analysis['overall_score']:.0f}/100")

        # Stage distribution
        if portfolio_analysis["stage_distribution"]:
            st.subheader("Lifecycle Stage Distribution")
            stage_df = pd.DataFrame(
                list(portfolio_analysis["stage_distribution"].items()),
                columns=["Stage", "Units"],
            )
            fig = px.bar(
                stage_df,
                x="Stage",
                y="Units",
                color="Stage",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig.update_layout(margin=dict(t=20, b=20), height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Per-project analysis
        st.subheader("🔬 Per-Project Analysis")
        for pa in portfolio_analysis["project_analyses"]:
            with st.expander(
                f"{lifecycle_emoji(pa['lifecycle_stage'])} {pa['project_name']} "
                f"— Score: {pa['lifecycle_score']:.0f}/100"
            ):
                pr_col1, pr_col2 = st.columns(2)

                with pr_col1:
                    st.write(f"**Project Type:** {pa['project_type'].replace('_', ' ').title()}")
                    st.write(f"**Lifecycle Stage:** {pa['lifecycle_stage']}")
                    st.write(f"**Permanence Score:** {pa['permanence_score']:.0f}/100")
                    st.write(f"**Co-effectiveness:** {pa['coeffectiveness_ratio']:.2f}")
                    st.write(f"**Vintage Quality:** {pa['vintage_adjustment']:.0%}")
                    st.write(f"**Geopolitical Risk:** {pa['geopolitical_risk']:.0f}/100")
                    st.write(f"**Est. Lifespan:** {pa['estimated_lifespan_years']} years")

                with pr_col2:
                    risk = pa["risk_assessment"]
                    st.write("**Risk Breakdown:**")
                    risk_df = pd.DataFrame({
                        "Factor": [
                            "Permanence", "Additionality", "Leakage",
                            "Registry", "Vintage", "Geopolitical", "Market",
                        ],
                        "Risk Score": [
                            risk.permanence_risk, risk.additionality_risk,
                            risk.leakage_risk, risk.registry_risk,
                            risk.vintage_risk, risk.geopolitical_risk,
                            risk.market_risk,
                        ],
                    })
                    fig = px.bar(
                        risk_df,
                        x="Risk Score",
                        y="Factor",
                        orientation="h",
                        color="Risk Score",
                        color_continuous_scale=["green", "yellow", "red"],
                        range_color=[0, 100],
                    )
                    fig.update_layout(margin=dict(t=10, b=10), height=250)
                    st.plotly_chart(fig, use_container_width=True)

                    if risk.risk_factors:
                        st.write("**Risk Factors:**")
                        for rf in risk.risk_factors:
                            st.write(f"  • {rf}")
                    if risk.mitigations:
                        st.write("**Mitigations:**")
                        for m in risk.mitigations:
                            st.write(f"  • {m}")

                if pa["recommendations"]:
                    st.write("**Recommendations:**")
                    for rec in pa["recommendations"]:
                        st.info(rec)


# ── Performance Trends ───────────────────────────────────────────────────

elif page == "📈 Performance Trends":
    st.header("📈 Performance Trends")

    snapshots = db.get_snapshot_history(user_id)

    if len(snapshots) < 2:
        st.info(
            "Need at least 2 portfolio snapshots to show trends. "
            "Snapshots are generated as you make transactions."
        )

        if holdings and st.button("📸 Generate Snapshot Now"):
            analyzer = PortfolioAnalyzer(holdings=holdings)
            snap = analyzer.generate_snapshot(user_id)
            db.save_snapshot(snap)
            st.success("Snapshot generated!")
            st.rerun()
    else:
        trends = compare_snapshots(snapshots)

        for trend in trends[:5]:
            st.subheader(
                f"📅 {trend['from_date'][:10]} → {trend['to_date'][:10]}"
            )
            t_cols = st.columns(len(trend["metrics"]))
            for col, metric in zip(t_cols, trend["metrics"]):
                direction_icon = {
                    "improved": "📈",
                    "worsened": "📉",
                    "stable": "➡️",
                }[metric["direction"]]
                col.metric(
                    f"{direction_icon} {metric['name']}",
                    f"{metric['current']:.1f}",
                    delta=f"{metric['delta']:.1f} ({metric['delta_percent']:.1f}%)",
                )


# ── Offset Optimizer ─────────────────────────────────────────────────────

elif page == "🎯 Offset Optimizer":
    st.header("🎯 Offset Allocation Optimizer")

    st.write(
        "Enter your carbon offset goal and budget to get an optimized "
        "allocation recommendation across available projects."
    )

    opt_col1, opt_col2, opt_col3 = st.columns(3)
    with opt_col1:
        target_co2 = st.number_input(
            "Target CO₂ offset (kg)",
            min_value=100.0,
            value=10000.0,
            step=100.0,
        )
    with opt_col2:
        budget = st.number_input(
            "Budget (USD)",
            min_value=10.0,
            value=500.0,
            step=50.0,
        )
    with opt_col3:
        risk_tolerance = st.selectbox(
            "Risk Tolerance",
            ["conservative", "medium", "aggressive"],
        )

    if st.button("🎯 Generate Allocation", type="primary"):
        available = db.list_projects(limit=100)
        allocations = optimize_offset_allocation(
            target_co2_kg=target_co2,
            budget_usd=budget,
            available_projects=available,
            risk_tolerance=risk_tolerance,
        )

        if not allocations:
            st.warning(
                "No suitable allocation found. Try increasing the budget "
                "or relaxing risk tolerance."
            )
        else:
            total_cost = sum(a["cost_usd"] for a in allocations)
            total_units = sum(a["units"] for a in allocations)

            st.success(
                f"Found allocation: **{total_units} units** across "
                f"**{len(allocations)} projects** for **{format_usd(total_cost)}**"
            )

            alloc_df = pd.DataFrame(allocations)
            st.dataframe(
                alloc_df[["name", "project_type", "units", "cost_usd", "registry", "country", "rationale"]],
                use_container_width=True,
            )

            # Cost breakdown chart
            fig = px.pie(
                alloc_df,
                values="cost_usd",
                names="name",
                title="Cost Allocation by Project",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(fig, use_container_width=True)


# ── Settings ──────────────────────────────────────────────────────────────

elif page == "⚙️ Settings":
    st.header("⚙️ Portfolio Settings")

    st.subheader("User ID")
    new_user_id = st.number_input(
        "User ID",
        min_value=1,
        value=user_id,
    )
    if new_user_id != user_id:
        st.session_state.user_id = int(new_user_id)
        st.rerun()

    st.divider()
    st.subheader("Database Management")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📸 Generate Portfolio Snapshot"):
            current_holdings = db.get_user_holdings(user_id)
            if current_holdings:
                analyzer = PortfolioAnalyzer(holdings=current_holdings)
                snap = analyzer.generate_snapshot(user_id)
                db.save_snapshot(snap)
                st.success("Snapshot saved!")
            else:
                st.warning("No holdings to snapshot.")

    with col2:
        if st.button("🗑️ Clear All Holdings", type="secondary"):
            st.warning("This feature is not implemented for safety.")

    st.divider()
    st.subheader("Export")

    current_holdings = db.get_user_holdings(user_id)
    if current_holdings:
        export_data = pd.DataFrame([h.to_dict() for h in current_holdings])
        csv = export_data.to_csv(index=False)
        st.download_button(
            "📥 Download Holdings CSV",
            csv,
            file_name="offset_holdings.csv",
            mime="text/csv",
        )


# ── Snapshot on page load if holdings exist ──────────────────────────────

if holdings and page == "📊 Dashboard Overview":
    # Auto-generate snapshot if latest is > 1 day old
    snapshots = db.get_snapshot_history(user_id, limit=1)
    should_snapshot = True
    if snapshots:
        latest = snapshots[0]
        age = datetime.utcnow() - latest.timestamp
        if age < timedelta(hours=24):
            should_snapshot = False

    if should_snapshot:
        analyzer = PortfolioAnalyzer(holdings=holdings)
        snap = analyzer.generate_snapshot(user_id)
        db.save_snapshot(snap)
