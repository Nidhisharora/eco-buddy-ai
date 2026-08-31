"""Streamlit page for Assessment History Advanced Search."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from src.core.database import get_assessments
from src.utils.assessment_history_utils import filter_assessments
from src.core.session_state_utils import ensure_session_state
from styles.theme import apply_theme

# --- Authentication & Setup ---
user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()

apply_theme()

st.title("📜 Assessment History")
st.markdown("Search, filter, and review your past environmental footprint assessments.")

# --- Session State Initialization ---
default_filters = {
    "history_keyword": "",
    "history_date_range": (date.today() - timedelta(days=365), date.today()),
    "history_eco_score": (0, 100),
    "history_sort_by": "Date",
    "history_sort_order": "Descending"
}
ensure_session_state(default_filters)

# --- Data Loading ---
raw_assessments = get_assessments(user_id)

if not raw_assessments:
    st.info("You haven't completed any assessments yet. Run an assessment on the Carbon Footprint page to get started!")
    st.stop()

# Convert to DataFrame
# Schema: id, user_id, date, created_at, transport, distance, electricity, diet, flights, footprint, eco_score, trip_id, factor_version
df_raw = pd.DataFrame(raw_assessments, columns=[
    "id", "user_id", "date", "created_at", "transport", "distance", 
    "electricity", "diet", "flights", "footprint", "eco_score", "trip_id", "factor_version"
])

# Display columns
DISPLAY_COLUMNS = [
    "date", "transport", "distance", "electricity", "diet", "flights", "footprint", "eco_score", "factor_version"
]

# --- Sidebar Filters ---
st.sidebar.header("🔍 Advanced Search")

# 1. Keyword Search
st.session_state.history_keyword = st.sidebar.text_input(
    "Keyword Search", 
    value=st.session_state.history_keyword,
    placeholder="e.g. Car, Vegetarian, v2...",
    help="Searches across transport, diet, and factor version."
)

# 2. Date Filter
date_val = st.sidebar.date_input(
    "Date Range",
    value=st.session_state.history_date_range,
    max_value=date.today()
)
if isinstance(date_val, tuple):
    st.session_state.history_date_range = date_val

# 3. Eco Score Filter
st.session_state.history_eco_score = st.sidebar.slider(
    "Eco Score Range",
    min_value=0,
    max_value=100,
    value=st.session_state.history_eco_score
)

# 4. Sorting
st.sidebar.markdown("---")
st.sidebar.subheader("Sort By")
st.session_state.history_sort_by = st.sidebar.selectbox(
    "Sort Column",
    options=["Date", "Eco Score", "Carbon Footprint"],
    index=["Date", "Eco Score", "Carbon Footprint"].index(st.session_state.history_sort_by)
)
st.session_state.history_sort_order = st.sidebar.radio(
    "Sort Order",
    options=["Descending", "Ascending"],
    index=["Descending", "Ascending"].index(st.session_state.history_sort_order)
)

if st.sidebar.button("Reset Filters"):
    for key, val in default_filters.items():
        st.session_state[key] = val
    st.rerun()

# --- Apply Filters ---
if isinstance(st.session_state.history_date_range, tuple) and len(st.session_state.history_date_range) == 2:
    start_dt, end_dt = st.session_state.history_date_range
    if start_dt > end_dt:
        st.error("❌ Invalid Date Range: Start date must be before or equal to the end date.")
        st.stop()
    
    filters = {
        "keyword": st.session_state.history_keyword,
        "date_range": (start_dt, end_dt),
        "eco_score_range": st.session_state.history_eco_score,
        "sort_by": st.session_state.history_sort_by,
        "sort_order": st.session_state.history_sort_order
    }
    
    filtered_df = filter_assessments(df_raw, filters)
    
    # --- Rendering Results ---
    if filtered_df.empty:
        st.warning("⚠️ No assessments match your current search and filter criteria.")
    else:
        st.success(f"✅ Found {len(filtered_df)} matching assessment(s).")
        
        # Select columns to display and rename them nicely
        display_df = filtered_df[DISPLAY_COLUMNS].copy()
        
        # Format date for better readability if desired
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d %H:%M')
        
        display_df = display_df.rename(columns={
            "date": "Date",
            "transport": "Transport",
            "distance": "Distance (km)",
            "electricity": "Electricity (kWh)",
            "diet": "Diet",
            "flights": "Flights",
            "footprint": "Footprint (kg CO₂)",
            "eco_score": "Eco Score",
            "factor_version": "Factor Version"
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("Please select a complete date range (start and end date).")

st.divider()
from src.utils.assessment_undo import render_assessment_undo_ui
render_assessment_undo_ui(user_id=user_id)

st.divider()
st.subheader("✏️ Edit or Finalize an Assessment")
st.caption(
    "Locking (#1467): edits carry the revision you last loaded, so a "
    "save is rejected instead of silently overwriting someone else's "
    "change if the assessment moved on in the meantime."
)

from src.core.database import (
    get_assessment_by_id,
    update_assessment,
    finalize_assessment,
    reopen_finalized_assessment,
)

edit_id = st.number_input(
    "Assessment ID", min_value=1, step=1, key="concurrency_edit_id"
)

if st.button("Load assessment"):
    st.session_state["concurrency_loaded"] = get_assessment_by_id(int(edit_id), user_id)
    st.session_state.pop("concurrency_conflict", None)

loaded = st.session_state.get("concurrency_loaded")
if loaded:
    if loaded["is_finalized"]:
        st.warning("This assessment is finalized and read-only.")
        if st.button("Reopen for editing"):
            result = reopen_finalized_assessment(loaded["id"], user_id, loaded["revision"])
            if result["status"] == "ok":
                st.success("Reopened. Reload it to edit.")
                st.session_state.pop("concurrency_loaded", None)
            elif result["status"] == "conflict":
                st.session_state["concurrency_conflict"] = result["current"]
            else:
                st.error(f"Could not reopen: {result['status']}")
    else:
        new_footprint = st.number_input(
            "Footprint (kg CO₂)", value=float(loaded["footprint"] or 0)
        )
        new_eco_score = st.number_input(
            "Eco Score", value=int(loaded["eco_score"] or 0)
        )

        col_save, col_finalize = st.columns(2)
        if col_save.button("Save changes"):
            result = update_assessment(
                loaded["id"],
                user_id,
                loaded["revision"],
                {"footprint": new_footprint, "eco_score": new_eco_score},
            )
            if result["status"] == "ok":
                st.success(f"Saved (now revision {result['revision']}).")
                st.session_state.pop("concurrency_loaded", None)
                st.session_state.pop("concurrency_conflict", None)
            elif result["status"] in ("conflict", "finalized"):
                st.session_state["concurrency_conflict"] = result["current"]
            else:
                st.error(f"Save failed: {result['status']}")

        if col_finalize.button("Finalize"):
            result = finalize_assessment(loaded["id"], user_id, loaded["revision"])
            if result["status"] == "ok":
                st.success("Finalized.")
                st.session_state.pop("concurrency_loaded", None)
            elif result["status"] in ("conflict", "finalized"):
                st.session_state["concurrency_conflict"] = result["current"]
            else:
                st.error(f"Finalize failed: {result['status']}")

conflict = st.session_state.get("concurrency_conflict")
if conflict:
    st.error(
        "This assessment changed since you loaded it, so your change was "
        "not applied. Here is the latest saved version:"
    )
    st.json(conflict)
    if st.button("Load latest & try again"):
        st.session_state["concurrency_loaded"] = conflict
        st.session_state.pop("concurrency_conflict", None)
        st.rerun()
