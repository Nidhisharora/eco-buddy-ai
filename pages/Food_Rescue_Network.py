"""
Food Rescue Network Page.
Streamlit page featuring a simulated live dashboard of surplus alerts, optimized pickup routes, and a community-wide "Food Waste Diverted" counter.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from food_rescue_matcher import FoodRescueMatcher
from surplus_logistics_engine import SurplusLogisticsEngine
from database import save_food_rescue_log, get_food_rescue_history

st.set_page_config(page_title="Food Rescue Network", page_icon="🥫", layout="wide")

st.title("🥫 Community-Scale Food Rescue & Surplus Redistribution Optimizer")
st.markdown(
    "Connect surplus food with those who need it. Optimize logistics to minimize transport emissions while maximizing food waste diversion."
)

# Initialize engines
if "matcher" not in st.session_state:
    st.session_state.matcher = FoodRescueMatcher()
    st.session_state.logistics = SurplusLogisticsEngine(st.session_state.matcher)

matcher = st.session_state.matcher
logistics = st.session_state.logistics

# --- Sidebar: Log Surplus ---
st.sidebar.header("🏪 Log Surplus Food")
with st.sidebar.form("log_donation_form"):
    donor = st.text_input("Donor Name (e.g., Local Bakery)", value="Main St Bakery")
    item_type = st.selectbox(
        "Food Category", ["produce", "canned", "dairy", "bakery", "prepared_meals"]
    )
    weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, value=5.0)
    spoilage = st.slider("Hours Until Spoilage", 1, 72, 24)
    location = st.selectbox("Donor Location", ["downtown", "westside", "university"])

    if st.form_submit_button("Register Surplus"):
        don_id = matcher.register_donation(donor, item_type, weight, spoilage)
        st.session_state.new_donation_id = don_id
        st.session_state.donor_location = location
        st.sidebar.success("Surplus registered! Finding best match...")
        st.rerun()

# --- Auto-Match New Donations ---
if "new_donation_id" in st.session_state:
    don_id = st.session_state.new_donation_id
    loc = st.session_state.donor_location

    impact = logistics.calculate_rescue_impact(don_id, loc)

    if "error" not in impact:
        st.success(
            f"✅ **Match Found!** {impact['recipient']} will accept this donation."
        )
        st.info(
            f"🌍 **Net Carbon Benefit:** {impact['net_carbon_benefit_kg']} kg CO₂e (Landfill avoided: {impact['landfill_avoided_kg']} kg - Transport: {impact['transport_emissions_kg']} kg)"
        )

        save_food_rescue_log(
            impact["recipient"], impact["weight_kg"], impact["net_carbon_benefit_kg"]
        )

    else:
        st.error(f"❌ **No Match Found:** {impact['error']}")

    # Clear session state to prevent re-triggering
    del st.session_state.new_donation_id
    del st.session_state.donor_location

# --- Main Dashboard ---
st.divider()
st.subheader("📊 Community Impact Dashboard")

community_impact = logistics.simulate_community_impact()

col1, col2, col3 = st.columns(3)
col1.metric(
    "Total Food Rescued", f"{community_impact['total_weight_rescued_kg']:.1f} kg"
)
col2.metric(
    "Landfill Methane Avoided",
    f"{community_impact['total_landfill_avoided_kg']:.1f} kg CO₂e",
)
col3.metric(
    "Net Carbon Benefit",
    f"{community_impact['net_community_carbon_benefit_kg']:.1f} kg CO₂e",
)

# Impact Visualization
fig = go.Figure(
    data=[
        go.Bar(
            name="Landfill Emissions Avoided",
            x=["Community Total"],
            y=[community_impact["total_landfill_avoided_kg"]],
            marker_color="#2ca02c",
        ),
        go.Bar(
            name="Transport Emissions",
            x=["Community Total"],
            y=[community_impact["total_transport_emissions_kg"]],
            marker_color="#d62728",
        ),
    ]
)
fig.update_layout(title="Net Carbon Impact of Food Rescue", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- Active Alerts ---
st.divider()
st.subheader("🚨 Active Surplus Alerts")
pending = matcher.get_pending_donations()

if pending:
    for p in pending:
        st.warning(
            f"**{p['donor_name']}** has **{p['weight_kg']} kg** of **{p['item_type']}** expiring in **{p['spoilage_hours']}** hours."
        )
else:
    st.success("🌟 All registered surplus has been successfully matched!")

# --- History ---
st.divider()
st.subheader("📜 Rescue Log History")
history = get_food_rescue_history()
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
else:
    st.info("No rescue operations logged yet.")
