"""
Climate Advocacy Page.
Streamlit page featuring a personalized action feed, pre-drafted advocacy message generators, and a long-term Civic Impact trend chart.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from civic_action_tracker import CivicActionTracker
from database import save_civic_action, get_civic_history

st.set_page_config(page_title="Climate Advocacy", page_icon="📢", layout="wide")

st.title("📢 Personalized Climate Advocacy & Civic Action Generator")
st.markdown(
    "Bridge the gap between personal carbon tracking and systemic change. Turn your footprint hotspots into targeted, actionable civic engagement."
)

# --- Configuration ---
st.sidebar.header("🎯 Your Footprint Hotspots")
st.sidebar.markdown(
    "Select your top emission sources to get personalized advocacy recommendations."
)
hotspot_1 = st.sidebar.selectbox(
    "Primary Hotspot",
    ["High Aviation", "High Home Energy", "High Diet (Meat)", "High Vehicle"],
)
hotspot_2 = st.sidebar.selectbox(
    "Secondary Hotspot",
    ["High Home Energy", "High Aviation", "High Vehicle", "High Diet (Meat)"],
)

if "tracker" not in st.session_state or st.session_state.get("hotspots_changed"):
    hotspots = [hotspot_1, hotspot_2]
    st.session_state.tracker = CivicActionTracker(user_hotspots=hotspots)
    st.session_state.hotspots_changed = False

tracker = st.session_state.tracker

# --- Main Dashboard ---
summary = tracker.get_tracker_summary()

col1, col2 = st.columns([1, 2])
with col1:
    st.metric(
        "Total Civic Impact Points", f"{summary['total_civic_impact_points']:.1f}"
    )
    st.markdown(f"**Actions Completed:** {summary['actions_completed_count']}")

with col2:
    # Civic Impact Trend Chart (Mock historical data)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=["Week 1", "Week 2", "Week 3", "Week 4"],
            y=[
                0,
                summary["total_civic_impact_points"] * 0.3,
                summary["total_civic_impact_points"] * 0.7,
                summary["total_civic_impact_points"],
            ],
            mode="lines+markers",
            name="Civic Impact Points",
            line=dict(color="#ff7f0e", width=3),
        )
    )
    fig.update_layout(
        title="Your Civic Impact Growth",
        xaxis_title="Time",
        yaxis_title="Points",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("📋 Your Personalized Action Feed")

actions = tracker.get_available_actions()

for i, action in enumerate(actions):
    with st.expander(
        f"**{action['name']}** (Target: {action['target']})", expanded=True
    ):
        st.markdown(f"**Policy Issue:** {action['policy_issue']}")
        st.markdown(f"**Linked to your hotspot:** {action['hotspot']}")
        st.markdown(
            f"**Action Type:** {action['action_type'].replace('_', ' ').title()}"
        )

        if action["action_type"] == "email_representative":
            st.text_area("Pre-drafted Email Template:", action["template"], height=100)

        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button(f"✅ Mark Complete", key=f"complete_{i}"):
                record = tracker.complete_action(action["name"], action["action_type"])
                save_civic_action(
                    action["name"], action["action_type"], record["points_awarded"]
                )
                st.success(
                    f"Awarded {record['points_awarded']:.1f} Civic Impact Points!"
                )
                st.rerun()
        with col_b:
            if action["action_type"] == "email_representative":
                st.button("📧 Open Email Client", key=f"email_{i}")
            elif action["action_type"] == "sign_petition":
                st.button("✍️ Go to Petition", key=f"petition_{i}")

# --- History ---
st.divider()
st.subheader("📜 Your Advocacy History")
history = get_civic_history()
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
else:
    st.info("No civic actions logged yet. Complete an action above to get started!")
