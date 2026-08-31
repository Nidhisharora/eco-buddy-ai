"""
Climate Resilience Page.
Streamlit page featuring an interactive risk radar chart, a step-by-step adaptation checklist, and a dynamic Resilience Score tracker.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from climate_risk_assessor import ClimateRiskAssessor
from adaptation_action_planner import AdaptationActionPlanner
from database import save_resilience_plan, get_resilience_history

st.set_page_config(page_title="Climate Resilience", page_icon="🛡️", layout="wide")

st.title("🛡️ Climate Resilience & Household Adaptation Planner")
st.markdown(
    "Evaluate your household's vulnerability to localized climate risks and build a tailored, actionable resilience plan."
)

# --- Input Section ---
st.sidebar.header("🏠 Household Profile")
region = st.sidebar.selectbox(
    "General Region",
    [
        "Coastal Florida",
        "Midwest Plains",
        "Southwest Desert",
        "Pacific Northwest",
        "Northeast Urban",
    ],
)
housing_type = st.sidebar.selectbox(
    "Housing Type",
    ["Mobile Home", "Older Wood Frame", "Modern Built", "Concrete Masonry"],
)
has_ac = st.sidebar.checkbox("Has Air Conditioning", value=True)
has_backup_power = st.sidebar.checkbox(
    "Has Backup Power (Generator/Battery)", value=False
)

if st.sidebar.button("🔍 Assess Climate Risks"):
    assessor = ClimateRiskAssessor(
        region=region,
        housing_type=housing_type,
        has_ac=has_ac,
        has_backup_power=has_backup_power,
    )
    risk_data = assessor.assess_risks()

    planner = AdaptationActionPlanner(
        hazard_scores=risk_data["hazard_scores"],
        base_resilience_score=risk_data["base_resilience_score"],
    )

    st.session_state.assessor = assessor
    st.session_state.planner = planner
    st.session_state.risk_data = risk_data

    save_resilience_plan(region, housing_type, risk_data["base_resilience_score"])
    st.sidebar.success("Risk assessment complete!")

# --- Results Display ---
if "planner" in st.session_state:
    planner = st.session_state.planner
    risk_data = st.session_state.risk_data
    summary = planner.get_action_summary()

    st.divider()
    st.subheader("📊 Multi-Hazard Risk Assessment")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(
            "Current Resilience Score",
            f"{summary['current_resilience_score']}/100",
            delta=f"{summary['current_resilience_score'] - summary['base_resilience_score']:+.1f}",
        )
        st.markdown(f"**Overall Risk Level:** {risk_data['overall_risk_level']}")
        st.markdown(
            f"**Region:** {risk_data['region']} | **Housing:** {risk_data['housing_type']}"
        )

    with col2:
        # Radar Chart for Hazard Scores
        hazards = list(risk_data["hazard_scores"].keys())
        scores = list(risk_data["hazard_scores"].values())

        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=scores,
                theta=[h.title() for h in hazards],
                fill="toself",
                name="Vulnerability Score (0-10)",
                marker_color="#d62728",
            )
        )
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            template="plotly_white",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()
    st.subheader("🛠️ Adaptation Action Plan")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### ✅ Completed Actions")
        if summary["completed_actions"]:
            for action in summary["completed_actions"]:
                st.success(f"- {planner.ADAPTATION_ACTIONS[action]['name']}")
        else:
            st.info("No actions completed yet. Start by checking off items below!")

    with col4:
        st.markdown("#### 📌 Recommended Next Steps")
        recommendations = summary["pending_recommendations"]
        if recommendations:
            for rec in recommendations[:3]:  # Show top 3
                with st.expander(
                    f"**{rec['name']}** ({rec['effort']} Effort | {rec['cost_range']})"
                ):
                    st.write(rec["description"])
                    st.write(f"**Targets:** {', '.join(rec['targets']).title()}")
                    if st.button(
                        f"Mark '{rec['name']}' as Completed",
                        key=f"complete_{rec['key']}",
                    ):
                        planner.complete_action(rec["key"])
                        st.rerun()
        else:
            st.success(
                "🌟 Excellent! You have completed all recommended adaptation actions."
            )

# --- History ---
st.divider()
st.subheader("📜 Past Resilience Assessments")
history = get_resilience_history()
if history:
    st.dataframe(pd.DataFrame(history), use_container_width=True)
else:
    st.info("No resilience plans saved yet.")
