
import math
from datetime import date

import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Daily Games | MindTrace",
    page_icon="🧠",
    layout="wide",
)

# --------------------------------------------------
# 2. FUTURISTIC DESIGN
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(92, 52, 160, 0.20),
                transparent 35%
            ),
            #0B0D17;
    }

    .game-hero {
        padding: 28px;
        border-radius: 20px;
        border: 1px solid rgba(145, 105, 255, 0.4);
        background: linear-gradient(
            120deg,
            rgba(91, 49, 158, 0.25),
            rgba(25, 40, 75, 0.35)
        );
        margin-bottom: 22px;
    }

    .game-label {
        color: #B9A0FF;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 3px;
    }

    .game-title {
        color: #F3F0FF;
        font-size: 38px;
        font-weight: 800;
        margin: 10px 0;
    }

    .game-description {
        color: #C0C3D4;
        font-size: 16px;
    }

    .game-card {
        padding: 22px;
        border: 1px solid rgba(145, 105, 255, 0.3);
        border-radius: 16px;
        background: rgba(22, 24, 43, 0.8);
        margin-bottom: 16px;
    }

    .muted-text {
        color: #A8ACC3;
        font-size: 14px;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #7855E8, #397DE8);
        border: none;
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 3. DAILY FERMI CHALLENGES
# --------------------------------------------------

# Reference answers are illustrative estimates,
# not verified official statistics.

puzzles = [
    {
        "title": "The Coffee Question",
        "category": "ESTIMATION",
        "question": (
            "How many cups of coffee are consumed "
            "in Tunisia in one day?"
        ),
        "unit": "cups per day",
        "reference": 3_000_000,
        "explanation": (
            "One possible estimate: about 12 million people, "
            "40% drinking coffee on a given day, and an average "
            "of roughly 0.6 cups per person among those drinkers. "
            "That gives about 2.9 million cups. The assumptions "
            "are deliberately rough."
        ),
        "hint": (
            "Start with Tunisia's population. Estimate what "
            "fraction drinks coffee on a typical day, then "
            "estimate how many cups each of those people drinks."
        ),
    },
    {
        "title": "The Supermarket Rush",
        "category": "EVERYDAY LOGIC",
        "question": (
            "How many customer visits might a busy supermarket "
            "receive in one day?"
        ),
        "unit": "visits per day",
        "reference": 1500,
        "explanation": (
            "Imagine 15 hours of operation and an average "
            "of 100 customer visits per hour. That produces "
            "about 1,500 visits. A real store could be far "
            "busier or quieter."
        ),
        "hint": (
            "Estimate how many hours the supermarket is open "
            "and how many customers enter each hour."
        ),
    },
    {
        "title": "The Smartphone Habit",
        "category": "HUMAN BEHAVIOUR",
        "question": (
            "How many times might one person unlock their "
            "smartphone in a day?"
        ),
        "unit": "unlocks per person per day",
        "reference": 80,
        "explanation": (
            "For this puzzle, 80 is an illustrative reference. "
            "You could estimate the number of times someone "
            "checks messages, social media, calls, and other "
            "apps throughout a typical day."
        ),
        "hint": (
            "Split the day into morning, afternoon, and evening. "
            "Estimate how often someone checks their phone "
            "during each period."
        ),
    },
    {
        "title": "The Pizza Estimate",
        "category": "NUMERICAL REASONING",
        "question": (
            "How many slices of pizza might people eat across "
            "Tunisia in one day?"
        ),
        "unit": "slices per day",
        "reference": 600_000,
        "explanation": (
            "A possible model is 12 million people, with "
            "around 2% eating pizza that day, averaging "
            "2.5 slices each. That gives about 600,000 slices. "
            "These are assumptions for the game, not measured data."
        ),
        "hint": (
            "Estimate how many people eat pizza on a given day, "
            "then multiply by their average number of slices."
        ),
    },
    {
        "title": "The Daily Word Count",
        "category": "HUMAN BEHAVIOUR",
        "question": (
            "Approximately how many spoken words might one "
            "adult say in a day?"
        ),
        "unit": "words per adult per day",
        "reference": 12000,
        "explanation": (
            "For this challenge, 12,000 words is an illustrative "
            "reference. Talking varies enormously by person, "
            "job, social situation, and day."
        ),
        "hint": (
            "Think about conversations at home, at school or "
            "work, and with friends. Estimate words per hour "
            "and how many hours you spend talking."
        ),
    },
]

# --------------------------------------------------
# 4. SELECT TODAY'S PUZZLE
# --------------------------------------------------

today = date.today()
puzzle_index = today.toordinal() % len(puzzles)
puzzle = puzzles[puzzle_index]
today_string = today.isoformat()

# Reset today's result if the date has changed.
if st.session_state.get("fermi_date") != today_string:
    st.session_state.fermi_date = today_string
    st.session_state.fermi_submitted = False
    st.session_state.fermi_estimate = None
    st.session_state.fermi_reasoning = ""
    st.session_state.fermi_score = None

# --------------------------------------------------
# 5. SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🧠 MindTrace")
    st.caption("Train your thinking.")
    st.divider()

    st.markdown("### 🎮 Daily Games")
    st.write("📍 Fermi Challenge")
    st.caption("A new estimation puzzle every day.")

    st.divider()
    st.caption("More games coming soon.")
    st.caption("• Pattern Breaker")
    st.caption("• Memory Rush")

# --------------------------------------------------
# 6. PAGE HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="game-hero">
        <div class="game-label">MINDTRACE // DAILY GAMES</div>
        <div class="game-title">Think beyond the obvious.</div>
        <div class="game-description">
            Train your estimation, assumptions, and reasoning
            with one new challenge each day.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    st.metric("Today's challenge", "01")

with col2:
    st.metric("Date", today.strftime("%d %b %Y"))

st.divider()

# --------------------------------------------------
# 7. FERMI CHALLENGE
# --------------------------------------------------

st.markdown("### ⚡ Fermi Challenge")
st.caption(f"{puzzle['category']}  •  Approximately 3–5 minutes")

st.markdown(
    f"""
    <div class="game-card">
        <div class="game-label">{puzzle['category']}</div>
        <h2>{puzzle['title']}</h2>
        <p style="font-size:20px;color:#F3F0FF;">
            {puzzle['question']}
        </p>
        <p class="muted-text">
            There isn't enough information to calculate an exact
            answer. Make sensible assumptions and build an estimate.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("💡 Need a hint?"):
    st.write(puzzle["hint"])

if not st.session_state.fermi_submitted:
    with st.form("fermi_answer_form"):
        estimate = st.number_input(
            f"Your estimate ({puzzle['unit']})",
            min_value=1,
            value=1000,
            step=1,
        )

        reasoning = st.text_area(
            "How did you arrive at your estimate?",
            placeholder=(
                "Example: I estimated the population, "
                "then the percentage of people who..."
            ),
            height=120,
        )

        submitted = st.form_submit_button(
            "SUBMIT ESTIMATE 🚀",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if len(reasoning.strip()) < 10:
            st.warning(
                "Add a little more reasoning before submitting. "
                "Explain at least one assumption you made."
            )
        else:
            reference = puzzle["reference"]
            estimate = max(1, int(estimate))

            # Compare answers by their order of magnitude.
            distance = abs(math.log10(estimate / reference))
            accuracy_points = max(0, 100 - distance * 35)

            # Reward explaining your assumptions.
            reasoning_bonus = min(
                10,
                len(reasoning.strip()) // 20 * 2,
            )

            score = min(
                100,
                round(accuracy_points + reasoning_bonus),
            )

            st.session_state.fermi_estimate = estimate
            st.session_state.fermi_reasoning = reasoning.strip()
            st.session_state.fermi_score = score
            st.session_state.fermi_submitted = True

            st.rerun()

# --------------------------------------------------
# 8. RESULTS AND FEEDBACK
# --------------------------------------------------

if st.session_state.fermi_submitted:
    estimate = st.session_state.fermi_estimate
    reference = puzzle["reference"]
    score = st.session_state.fermi_score

    factor = max(
        estimate / reference,
        reference / estimate,
    )

    st.divider()
    st.markdown("## 🏆 Challenge complete!")

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        st.metric("Reasoning score", f"{score}/100")

    with result_col2:
        st.metric("Reference estimate", f"{reference:,}")

    st.write(f"**Your estimate:** {estimate:,} {puzzle['unit']}")
    st.write(
        f"**Distance from reference:** approximately "
        f"{factor:.2f}×"
    )

    if factor <= 2:
        st.success(
            "Excellent estimation! You were within a factor "
            "of two of the reference."
        )
    elif factor <= 10:
        st.info(
            "Good attempt! Your estimate was within one "
            "order of magnitude. Refine your assumptions "
            "to get closer."
        )
    else:
        st.warning(
            "This estimate was quite far from the reference. "
            "Try breaking the problem into smaller quantities."
        )

    st.markdown("### 🧩 How you could solve it")
    st.write(puzzle["explanation"])

    with st.expander("Review your reasoning"):
        st.write(st.session_state.fermi_reasoning)

    st.caption(
        "The score rewards closeness to an illustrative reference "
        "and the effort to explain your assumptions. It is a game "
        "score, not a validated measure of intelligence."
    )

# --------------------------------------------------
# 9. FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "MINDTRACE • DAILY GAMES • Estimate. Reason. Improve."
)
