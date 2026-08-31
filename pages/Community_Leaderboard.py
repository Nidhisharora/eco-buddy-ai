"""
Community Leaderboard & Team Carbon Challenges

Interactive Streamlit page for global leaderboards, team management,
and team-based sustainability challenges.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from src.community import leaderboard_service as lbs
from styles.theme import apply_theme

# ---------------------------------------------------------------------------
# Page config & theme
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Community Leaderboard", page_icon="🏆", layout="wide")
apply_theme()

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

# Initialize DB tables and seed data
lbs.init_leaderboard_tables()
lbs.seed_sample_teams()
lbs.seed_sample_challenges()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    "<div class='section-header'>🏆 Community Leaderboard & Team Challenges</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Compete with other eco-warriors, join or create teams, and take on "
    "team challenges to maximize your collective carbon savings!"
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🏆 Navigation")
    page_tab = st.radio(
        "Section",
        ["📊 Global Leaderboard", "👥 Teams", "🎯 Team Challenges", "📈 My Stats"],
        label_visibility="collapsed",
    )

# ===========================================================================
# TAB 1: Global Leaderboard
# ===========================================================================

if page_tab == "📊 Global Leaderboard":
    st.markdown("## 📊 Global Leaderboard")

    col_filter, col_period = st.columns([2, 1])
    with col_filter:
        category = st.selectbox(
            "Rank by",
            options=list(lbs.LEADERBOARD_CATEGORIES.keys()),
            format_func=lambda x: lbs.LEADERBOARD_CATEGORIES[x],
        )
    with col_period:
        time_period = st.selectbox("Time Period", ["All Time", "This Month", "This Week"])

    leaderboard = lbs.get_global_leaderboard(category, limit=50)

    my_pos = lbs.get_user_leaderboard_position(user_id, category)
    if my_pos:
        st.info(
            f"📍 Your position: **#{my_pos.rank}** | "
            f"Carbon saved: **{my_pos.carbon_saved_kg:.1f} kg** | "
            f"Streak: **{my_pos.streak_days} days**"
        )

    if not leaderboard:
        st.info("No leaderboard data yet. Start logging your eco-activities!")
    else:
        top_10 = leaderboard[:10]
        fig = px.bar(
            pd.DataFrame([e.to_dict() for e in top_10]),
            x="username",
            y="carbon_saved_kg",
            color="level",
            color_continuous_scale="green",
            labels={"carbon_saved_kg": "Carbon Saved (kg)", "username": "User"},
            title="Top 10 Carbon Savers",
        )
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Full Rankings")
        df_data = []
        for entry in leaderboard:
            medal = ""
            if entry.rank == 1:
                medal = "🥇"
            elif entry.rank == 2:
                medal = "🥈"
            elif entry.rank == 3:
                medal = "🥉"
            else:
                medal = f"#{entry.rank}"

            df_data.append({
                "Rank": medal,
                "User": entry.username,
                "Level": f"Lvl {entry.level}",
                "Carbon Saved (kg)": f"{entry.carbon_saved_kg:.1f}",
                "Streak": f"🔥 {entry.streak_days}d",
                "Badges": entry.badges_count,
                "Team": entry.team_name or "—",
            })

        st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)

        # Category breakdown for top user
        if leaderboard:
            top_user = leaderboard[0]
            st.markdown(f"### 🏅 {top_user.username}'s Savings Breakdown")
            cats = lbs.get_global_leaderboard("transport", 1)
            cats2 = lbs.get_global_leaderboard("energy", 1)
            cats3 = lbs.get_global_leaderboard("diet", 1)
            cats4 = lbs.get_global_leaderboard("water", 1)

            breakdown = {
                "Transport": next(
                    (e.carbon_saved_kg for e in cats if e.user_id == top_user.user_id), 0
                ),
                "Energy": next(
                    (e.carbon_saved_kg for e in cats2 if e.user_id == top_user.user_id), 0
                ),
                "Diet": next(
                    (e.carbon_saved_kg for e in cats3 if e.user_id == top_user.user_id), 0
                ),
                "Water": next(
                    (e.carbon_saved_kg for e in cats4 if e.user_id == top_user.user_id), 0
                ),
            }

            fig_pie = px.pie(
                names=list(breakdown.keys()),
                values=list(breakdown.values()),
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig_pie.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ===========================================================================
# TAB 2: Teams
# ===========================================================================

elif page_tab == "👥 Teams":
    st.markdown("## 👥 Sustainability Teams")

    my_team = lbs.get_user_team(user_id)
    all_teams = lbs.get_all_teams()

    if my_team:
        st.success(f"🌿 You are a member of **{my_team.icon} {my_team.name}**")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Members", my_team.member_count)
        col2.metric("Carbon Saved", f"{my_team.total_carbon_saved_kg:.1f} kg")
        col3.metric("Avg Eco Score", f"{my_team.avg_eco_score:.0f}")
        col4.metric("Challenge Wins", my_team.challenge_wins)

        st.markdown("### 👥 Team Members")
        members = lbs.get_team_members(my_team.team_id)
        if members:
            df_members = pd.DataFrame(members)
            df_members.columns = [
                "User ID", "Username", "Role", "Joined",
                "Carbon Saved (kg)", "Eco Score", "Level",
            ]
            st.dataframe(df_members, use_container_width=True, hide_index=True)

        if members:
            fig_team = px.bar(
                df_members,
                x="Username",
                y="Carbon Saved (kg)",
                color="Role",
                color_discrete_map={"captain": "#FFD700", "member": "#4CAF50"},
                title=f"{my_team.name} — Member Contributions",
            )
            fig_team.update_layout(
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_team, use_container_width=True)

        if st.button("🚪 Leave Team"):
            success, msg = lbs.leave_team(user_id)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        st.info("You are not on a team yet. Join or create one below!")

        with st.expander("➕ Create a New Team", expanded=not all_teams):
            with st.form("create_team"):
                team_name = st.text_input("Team Name", max_chars=40)
                team_desc = st.text_area("Description", max_chars=200)
                team_icon = st.selectbox("Icon", lbs.TEAM_ICONS, index=0)
                submitted = st.form_submit_button("Create Team", type="primary")
                if submitted:
                    if not team_name.strip():
                        st.error("Team name is required.")
                    else:
                        tid = lbs.create_team(
                            team_name.strip(), team_desc.strip(), user_id, team_icon
                        )
                        st.success(f"Team '{team_name}' created! 🎉")
                        st.rerun()

        if all_teams:
            st.markdown("### Browse Teams")
            for team in all_teams:
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    with c1:
                        st.markdown(f"**{team.icon} {team.name}**")
                        st.caption(team.description)
                    with c2:
                        st.metric("Members", f"{team.member_count}/{team.max_members}")
                    with c3:
                        st.metric("Carbon Saved", f"{team.total_carbon_saved_kg:.0f} kg")
                    with c4:
                        if team.is_open and team.member_count < team.max_members:
                            if st.button("Join", key=f"join_{team.team_id}"):
                                success, msg = lbs.join_team(user_id, team.team_id)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.caption("🔒 Closed / Full")
                    st.divider()

# ===========================================================================
# TAB 3: Team Challenges
# ===========================================================================

elif page_tab == "🎯 Team Challenges":
    st.markdown("## 🎯 Team Carbon Challenges")

    my_team = lbs.get_user_team(user_id)

    ch_filter = st.radio("Filter", ["Active", "Upcoming", "Completed"], horizontal=True)
    status_map = {"Active": "active", "Upcoming": "upcoming", "Completed": "completed"}
    challenges = lbs.get_team_challenges(status=status_map[ch_filter])

    if not challenges:
        st.info(f"No {ch_filter.lower()} team challenges right now.")
    else:
        for ch in challenges:
            with st.expander(
                f"{ch.icon} {ch.title} — {ch.target_kg} kg target — {ch.duration_days} days"
            ):
                st.write(f"**{ch.description}**")
                st.caption(
                    f"Category: {ch.category.title()} | "
                    f"XP Reward: {ch.xp_reward} XP | "
                    f"Ends: {ch.ends_at[:10]}"
                )

                rankings = lbs.get_challenge_leaderboard(ch.challenge_id)
                if rankings:
                    df_rank = pd.DataFrame(rankings)
                    df_rank.columns = [
                        "Rank", "Team ID", "Team", "Icon",
                        "Carbon Saved (kg)", "Participants", "Last Updated",
                    ]
                    st.dataframe(
                        df_rank[["Rank", "Team", "Icon", "Carbon Saved (kg)", "Participants"]],
                        use_container_width=True,
                        hide_index=True,
                    )

                    fig_ch = px.bar(
                        df_rank,
                        x="Team",
                        y="Carbon Saved (kg)",
                        color="Rank",
                        color_continuous_scale="RdYlGn_r",
                        title=f"{ch.title} — Progress",
                    )
                    fig_ch.update_layout(
                        template="plotly_dark",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig_ch, use_container_width=True)

                    if my_team:
                        team_progress = next(
                            (r for r in rankings if r["team_id"] == my_team.team_id),
                            None,
                        )
                        if team_progress:
                            progress_pct = min(
                                team_progress["carbon_saved"] / ch.target_kg, 1.0
                            )
                            st.progress(
                                progress_pct,
                                text=f"Your team: {team_progress['carbon_saved']:.1f} / {ch.target_kg} kg",
                            )
                else:
                    st.info("No progress data yet for this challenge.")

    st.markdown("---")
    with st.expander("➕ Create a Team Challenge"):
        with st.form("create_challenge"):
            ch_title = st.text_input("Challenge Title", max_chars=60)
            ch_desc = st.text_area("Description", max_chars=200)
            ch_category = st.selectbox(
                "Category", ["overall", "transport", "energy", "diet", "water"]
            )
            ch_target = st.number_input(
                "Target (kg CO₂ saved)", min_value=1.0, value=50.0, step=5.0
            )
            ch_days = st.number_input("Duration (days)", min_value=1, value=7, step=1)
            ch_xp = st.number_input("XP Reward", min_value=10, value=200, step=10)
            ch_icon = st.selectbox(
                "Icon",
                ["🏆", "⚡", "🌍", "🚲", "🥗", "💧", "🔥", "🌱"],
                index=0,
            )
            ch_submit = st.form_submit_button("Create Challenge", type="primary")
            if ch_submit:
                if not ch_title.strip():
                    st.error("Title is required.")
                else:
                    cid = lbs.create_team_challenge(
                        ch_title.strip(), ch_desc.strip(), ch_category,
                        ch_target, ch_days, ch_xp, ch_icon,
                    )
                    st.success(f"Challenge '{ch_title}' created! 🎉")
                    st.rerun()

# ===========================================================================
# TAB 4: My Stats
# ===========================================================================

elif page_tab == "📈 My Stats":
    st.markdown("## 📈 My Leaderboard Stats")

    my_entry = lbs.get_user_leaderboard_position(user_id)
    my_team = lbs.get_user_team(user_id)

    col1, col2, col3, col4 = st.columns(4)
    if my_entry:
        col1.metric("🏆 Rank", f"#{my_entry.rank}")
        col2.metric("🌍 Carbon Saved", f"{my_entry.carbon_saved_kg:.1f} kg")
        col3.metric("🔥 Streak", f"{my_entry.streak_days} days")
        col4.metric("🎖️ Badges", my_entry.badges_count)
    else:
        col1.metric("🏆 Rank", "Unranked")
        col2.metric("🌍 Carbon Saved", "0 kg")
        col3.metric("🔥 Streak", "0 days")
        col4.metric("🎖️ Badges", "0")

    st.markdown("---")

    st.markdown("### 📝 Log Carbon Savings")
    st.caption(
        "Record your carbon savings to improve your leaderboard position and help your team!"
    )

    with st.form("log_carbon"):
        log_cat = st.selectbox(
            "Category",
            ["transport", "energy", "diet", "water"],
            format_func=lambda x: {
                "transport": "🚗 Transport",
                "energy": "⚡ Energy",
                "diet": "🥗 Diet",
                "water": "💧 Water",
            }[x],
        )
        log_amount = st.number_input(
            "Amount saved (kg CO₂)", min_value=0.1, value=1.0, step=0.5
        )
        log_desc = st.text_input("Description (optional)", max_chars=100)
        log_submit = st.form_submit_button("Log Savings", type="primary")
        if log_submit:
            success = lbs.log_carbon_saving(user_id, log_cat, log_amount, log_desc)
            if success:
                st.success(f"Logged {log_amount} kg CO₂ saved in {log_cat}! 🌿")
                st.rerun()
            else:
                st.error("Failed to log savings. Please try again.")

    if my_team:
        st.markdown(f"### 🌿 My Team: {my_team.icon} {my_team.name}")
        st.write(my_team.description)
        members = lbs.get_team_members(my_team.team_id)
        if members:
            df_m = pd.DataFrame(members)
            df_m.columns = [
                "User ID", "Username", "Role", "Joined",
                "Carbon Saved (kg)", "Eco Score", "Level",
            ]
            my_member = df_m[df_m["User ID"] == user_id]
            if not my_member.empty:
                my_saving = my_member.iloc[0]["Carbon Saved (kg)"]
                team_total = my_team.total_carbon_saved_kg
                contribution = (my_saving / team_total * 100) if team_total > 0 else 0
                st.metric("Your Team Contribution", f"{contribution:.1f}%")

    st.markdown("### 📊 Your Category Performance")
    cat_data = []
    for cat_key, cat_label in lbs.LEADERBOARD_CATEGORIES.items():
        if cat_key in ("overall", "streak"):
            continue
        entry = lbs.get_user_leaderboard_position(user_id, cat_key)
        cat_data.append({
            "Category": cat_label,
            "Carbon Saved (kg)": entry.carbon_saved_kg if entry else 0,
            "Rank": entry.rank if entry else "Unranked",
        })

    if cat_data:
        df_cats = pd.DataFrame(cat_data)
        fig_cats = px.bar(
            df_cats,
            x="Category",
            y="Carbon Saved (kg)",
            color="Carbon Saved (kg)",
            color_continuous_scale="greens",
            title="Your Savings by Category",
        )
        fig_cats.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_cats, use_container_width=True)
