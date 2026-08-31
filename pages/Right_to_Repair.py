"""
Right to Repair Page.
Streamlit page where users can log broken items, view repairability scores, access simulated repair guides, and track cumulative Repair Impact.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from product_lifecycle_tracker import ProductLifecycleTracker
from repairability_index_db import RepairabilityIndexDB
from database import save_repair_log, get_repair_history

st.set_page_config(page_title="Right to Repair", page_icon="🔧", layout="wide")

st.title("🔧 Consumer Product Repairability Index & Impact Tracker")
st.markdown("Fight planned obsolescence! Evaluate the repairability of your items, access repair resources, and track the embodied carbon you save by choosing repair over replacement.")

tracker = ProductLifecycleTracker()
db = RepairabilityIndexDB()
products = db.get_all_products()

# --- Sidebar: Log a Repair ---
st.sidebar.header("🛠️ Log a Repair")
with st.sidebar.form("log_repair_form"):
    product = st.selectbox(
        "Product", 
        options=products, 
        format_func=lambda x: db.get_product_display_name(x)
    )
    
    # Dynamic part selection based on common failures
    details = db.get_product_details(product)
    default_failure = details["common_failures"][0] if details else "other"
    
    part = st.selectbox("Issue / Replaced Part", ["other"] + (details["common_failures"] if details else []))
    custom_part = st.text_input("Or specify custom part", value="")
    final_part = custom_part if custom_part else part
    
    success = st.radio("Was the repair successful?", ["Yes", "No"])
    
    if st.form_submit_button("Log Repair"):
        try:
            record = tracker.log_repair(product, final_part, success == "Yes")
            save_repair_log(product, final_part, record["status"], record["embodied_carbon_avoided_kg"])
            
            if success == "Yes":
                st.sidebar.success(f"Awesome! You saved ~{record['embodied_carbon_avoided_kg']} kg of CO₂e.")
            else:
                st.sidebar.warning("Repair failed, but the attempt is logged. Don't give up!")
            st.rerun()
        except ValueError as e:
            st.sidebar.error(str(e))

# --- Main Dashboard ---
impact = tracker.get_cumulative_impact()

st.subheader("🌍 Your Cumulative Repair Impact")
col1, col2, col3 = st.columns(3)
col1.metric("Successful Repairs", impact["successful_repairs"])
col2.metric("Embodied Carbon Saved", f"{impact['total_carbon_saved_kg']:.1f} kg CO₂e")
col3.metric("Waste Diverted", f"{impact['estimated_waste_diverted_kg']:.1f} kg")

# Impact Chart
fig = go.Figure(data=[
    go.Bar(name="Embodied Carbon Saved", x=["Total Impact"], y=[impact["total_carbon_saved_kg"]], marker_color="#2ca02c"),
    go.Bar(name="Carbon Cost of Parts", x=["Total Impact"], y=[impact["total_parts_carbon_kg"]], marker_color="#ff7f0e")
])
fig.update_layout(title="Net Carbon Impact of Repairs", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- Product Explorer ---
st.divider()
st.subheader("🔍 Product Repairability Explorer")
st.markdown("Search for a product to see its repairability score, common failures, and resources.")

search_product = st.selectbox("Select a Product to Explore", options=products, format_func=lambda x: db.get_product_display_name(x))

if search_product:
    details = db.get_product_details(search_product)
    resources = tracker.get_repair_resources(search_product)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### {details['name']}")
        st.markdown(f"**Category:** {details['category'].title()}")
        
        # Repairability Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=details["repairability_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Repairability Score (1-10)"},
            gauge={
                'axis': {'range': [1, 10]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [1, 4], 'color': "#f8d7da"},
                    {'range': [4, 7], 'color': "#fff3cd"},
                    {'range': [7, 10], 'color': "#d4edda"}
                ]
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with col_b:
        st.markdown("#### 📋 Repair Profile")
        st.markdown(f"- **Embodied Carbon:** {details['embodied_carbon_kg']} kg CO₂e")
        st.markdown(f"- **Parts Availability:** {details['parts_availability']}")
        st.markdown(f"- **Common Failures:** {resources['common_issues']}")
        st.markdown(f"- **Parts Carbon Cost:** ~{tracker.PART_CARBON_COSTS.get(resources['common_issues'].split(',')[0].strip().lower(), 5.0)} kg CO₂e")
        
        st.markdown("#### 🔗 Helpful Resources")
        st.markdown(f"- [Official/iFixit Repair Guide]({resources['guide']})")
        st.info(resources["parts_note"])

# --- History ---
st.divider()
st.subheader("📜 Repair Log History")
history = get_repair_history()
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
else:
    st.info("No repairs logged yet. Start fixing things!")
