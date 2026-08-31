"""
Sustainable Finance Page.
Streamlit page featuring a portfolio carbon breakdown chart, a "green swap" recommendation engine, and an alignment score.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from sustainable_portfolio_analyzer import SustainablePortfolioAnalyzer
from asset_carbon_db import AssetCarbonDB
from database import save_portfolio_analysis, get_portfolio_history

st.set_page_config(page_title="Sustainable Finance", page_icon="💹", layout="wide")

st.title("💹 Sustainable Finance Portfolio Analyzer & Green Rebalancing Engine")
st.markdown(
    "Estimate the 'financed emissions' of your investments and discover how to align your portfolio with climate goals."
)

analyzer = SustainablePortfolioAnalyzer()
db = AssetCarbonDB()
assets = db.get_all_assets()

# --- Sidebar: Portfolio Builder ---
st.sidebar.header("💼 Build Your Portfolio")
with st.sidebar.form("add_holding_form"):
    asset = st.selectbox(
        "Asset", options=assets, format_func=lambda x: db.get_asset_display_name(x)
    )
    amount = st.number_input(
        "Amount Invested ($)", min_value=100.0, step=500.0, value=5000.0
    )

    if st.form_submit_button("Add Holding"):
        analyzer.add_holding(asset, amount)
        st.sidebar.success("Holding added!")
        st.rerun()

if st.sidebar.button("🔍 Analyze Portfolio"):
    analysis = analyzer.analyze_portfolio()
    st.session_state.portfolio_analysis = analysis
    save_portfolio_analysis(
        analysis["total_invested_usd"],
        analysis["total_emissions_tonnes"],
        analysis["weighted_alignment_score"],
    )
    st.sidebar.success("Analysis complete!")

# --- Main Dashboard ---
if "portfolio_analysis" in st.session_state:
    analysis = st.session_state.portfolio_analysis

    if analysis["total_invested_usd"] == 0:
        st.info("Add holdings in the sidebar to see your portfolio analysis.")
    else:
        st.divider()
        st.subheader("📊 Portfolio Climate Impact")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested", f"${analysis['total_invested_usd']:,.0f}")
        col2.metric(
            "Financed Emissions",
            f"{analysis['total_emissions_tonnes']:.2f} tonnes CO₂e",
        )

        # Color code alignment score
        score = analysis["weighted_alignment_score"]
        delta_color = "normal" if score >= 70 else "inverse"
        col3.metric(
            "Paris Alignment Score", f"{score:.0f}/100", delta_color=delta_color
        )

        # Emissions Breakdown Chart
        st.markdown("### 🏭 Emissions by Holding")
        df_breakdown = pd.DataFrame(analysis["asset_breakdown"])

        fig = go.Figure(
            data=[
                go.Bar(
                    x=df_breakdown["name"],
                    y=df_breakdown["emissions_tonnes"],
                    text=df_breakdown["emissions_tonnes"],
                    textposition="auto",
                    marker_color="#1f77b4",
                )
            ]
        )
        fig.update_layout(
            title="Financed Emissions Breakdown (tonnes CO₂e)",
            xaxis_title="Asset",
            yaxis_title="Emissions (tonnes)",
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Green Swap Engine
        st.divider()
        st.subheader("🔄 Green Asset Rebalancing Engine")
        st.markdown(
            "Identify high-carbon 'hotspots' and simulate swapping them for verified green alternatives."
        )

        if analysis["hotspots"]:
            hotspot = analysis["hotspots"][0]
            st.markdown(
                f"#### 🔥 Top Emission Hotspot: **{hotspot['name']}** ({hotspot['emissions_tonnes']:.2f} tonnes)"
            )

            alternatives = db.find_green_alternatives(hotspot["asset_key"])

            if alternatives:
                alt_options = {alt["name"]: alt["key"] for alt in alternatives}
                selected_alt_name = st.selectbox(
                    "Select a Green Alternative", options=list(alt_options.keys())
                )
                selected_alt_key = alt_options[selected_alt_name]

                max_swap = min(
                    hotspot["amount_usd"], 10000.0
                )  # Cap mock swap at $10k or holding amount
                swap_amount = st.slider(
                    f"Amount to swap from {hotspot['name']} ($)",
                    500.0,
                    max_swap,
                    5000.0,
                    step=500.0,
                )

                if st.button("Simulate Swap"):
                    sim_result = analyzer.simulate_rebalance(
                        hotspot["asset_key"], selected_alt_key, swap_amount
                    )

                    st.success(f"**Swap Simulated!**")
                    st.markdown(
                        f"- **From:** {sim_result['from_asset']} ➔ **To:** {sim_result['to_asset']}"
                    )
                    st.markdown(
                        f"- **Emissions Reduced:** {sim_result['emissions_reduced_tonnes']:.3f} tonnes CO₂e"
                    )
                    st.markdown(
                        f"- **New Portfolio Emissions:** {sim_result['new_portfolio_emissions_tonnes']:.3f} tonnes"
                    )
                    st.markdown(
                        f"- **New Alignment Score:** {sim_result['new_alignment_score']:.1f}/100"
                    )
            else:
                st.success("✅ This holding is already a relatively low-carbon option!")
        else:
            st.success("✅ Your portfolio has no major emission hotspots.")

# --- History ---
st.divider()
st.subheader("📜 Past Portfolio Analyses")
history = get_portfolio_history()
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
else:
    st.info("No portfolio analyses saved yet.")
