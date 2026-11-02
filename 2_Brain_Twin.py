
import json

import streamlit as st
import brain_twin_db as db
import plotly.graph_objects as go

st.set_page_config(
    page_title="MindTrace | Brain Twin",
    page_icon="🧠",
    layout="wide",
)

# Require a signed-in user on this page too.
user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("Please sign in to view your Brain Twin.")
    st.page_link("app.py", label="Go to sign in")
    st.stop()

username = st.session_state.get("username", "User")

st.title("🧠 Your Brain Twin")
st.caption(
    f"Welcome, {username}. Your personal cognitive practice history."
)

st.info(
    "Your Cognitive Index reflects performance on MindTrace's "
    "experimental tasks. It is not a validated IQ score."
)

try:
    history = db.get_user_history(user_id)
except Exception:
    st.error("Could not load your assessment history.")
    st.stop()

st.divider()
st.subheader("🔐 My data")
st.download_button(
    "Export my history (JSON)",
    data=json.dumps(history, indent=2),
    file_name="mindtrace_history.json",
    mime="application/json",
    use_container_width=True,
)

confirm_delete = st.checkbox(
    "I understand that deleting my account permanently removes my "
    "account and assessment history."
)

if st.button(
    "Delete my account and data",
    disabled=not confirm_delete,
    use_container_width=True,
):
    try:
        db.delete_user(user_id)
        st.session_state.clear()
        st.rerun()
    except Exception:
        st.error("Your account could not be deleted. Please try again.")

if not history:
    st.subheader("Your journey starts here")
    st.write(
        "Complete your first assessment to create your baseline. "
        "Your results will appear here after they have been saved."
    )
    st.page_link("app.py", label="Start an assessment")
    st.stop()

# History is returned oldest first.
latest = history[-1]

first_score = history[0]["cognitive_index"]
latest_score = latest["cognitive_index"]
change = latest_score - first_score

col1, col2, col3 = st.columns(3)

col1.metric(
    "Assessments completed",
    len(history),
)

col2.metric(
    "Latest Cognitive Index",
    f"{latest_score}/100",
)

col3.metric(
    "Change since first attempt",
    f"{change:+d} points",
    help="Latest score minus first recorded score.",
)

st.divider()

# Progress curve.
st.subheader("📈 Your progress")

if len(history) >= 2:
    chart_data = {
        "Cognitive Index": [
            item["cognitive_index"] for item in history
        ]
    }

    st.line_chart(chart_data, y="Cognitive Index", height=300)

    st.caption(
        "Each point represents a completed assessment, "
        "ordered from oldest to newest."
    )
else:
    st.write(
        "Complete another assessment to see your progress curve."
    )
    st.bar_chart(
        {"Cognitive Index": [latest_score]},
        height=200,
    )

st.divider()

# Category scores across all recorded attempts.
st.subheader("🗺️ Category performance over time")

category_order = []

for attempt in history:
    for category in attempt.get("category_scores", {}):
        if category not in category_order:
            category_order.append(category)

if category_order:
    heatmap_values = []

    for category in category_order:
        row = []

        for attempt in history:
            raw_score = attempt.get("category_scores", {}).get(category)

            if isinstance(raw_score, dict):
                row.append(raw_score.get("score"))
            elif isinstance(raw_score, (int, float)):
                row.append(raw_score)
            else:
                row.append(None)

        heatmap_values.append(row)

    heatmap = go.Figure(
        data=go.Heatmap(
            z=heatmap_values,
            x=[f"Attempt {number}" for number in range(1, len(history) + 1)],
            y=category_order,
            zmin=0,
            zmax=100,
            colorscale="Viridis",
            colorbar=dict(title="Score (%)"),
            hovertemplate=(
                "<b>%{y}</b><br>%{x}<br>Score: %{z}%"
                "<extra></extra>"
            ),
        )
    )
    heatmap.update_layout(
        title="Category scores by assessment",
        height=max(300, 55 * len(category_order) + 120),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(
        heatmap,
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption(
        "Blank cells indicate that a category was not recorded in that "
        "assessment."
    )
else:
    st.info("No category scores are available for the heatmap.")

st.divider()

# Most recent category profile.
st.subheader("🎯 Latest cognitive profile")

category_scores = latest.get("category_scores", {})

if category_scores:
    score_data = {
        category: (
            details.get("score", 0)
            if isinstance(details, dict)
            else details
        )
        for category, details in category_scores.items()
    }

    st.bar_chart(score_data, height=300)

    for category, details in category_scores.items():
        if isinstance(details, dict):
            score = details.get("score", 0)
            correct = details.get("correct", 0)
            total = details.get("total", 0)
        else:
            score = details
            correct = "-"
            total = "-"

        st.write(f"**{category}** — {score}% ({correct}/{total})")
else:
    st.warning("No category scores were recorded for this assessment.")

st.divider()

# Assessment history table.
st.subheader("📚 Assessment history")

table_rows = []

for number, item in enumerate(history, start=1):
    table_rows.append({
        "Attempt": number,
        "Completed (UTC)": item["completed_at"],
        "Cognitive Index": item["cognitive_index"],
        "Correct": (
            f'{item["correct_count"]}/{item["total_questions"]}'
        ),
        "Average response (s)": round(item["average_seconds"], 2),
    })

st.dataframe(
    table_rows,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Privacy: this page requests history using your signed-in "
    "user ID. Only records associated with that ID are displayed."
)
