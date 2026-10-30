
import streamlit as st
from google import genai

# -----------------------------
# 1. PAGE SETUP
# -----------------------------
st.set_page_config(
    page_title="MindTrace",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 MindTrace")
st.subheader("Daily brain games. Better thinking.")

st.write(
    "Solve a challenge, explain your reasoning, "
    "and get feedback from your AI Thinking Coach."
)

# -----------------------------
# 2. SESSION DATA
# -----------------------------
if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "total_score" not in st.session_state:
    st.session_state.total_score = 0

if "hints_used" not in st.session_state:
    st.session_state.hints_used = 0

if "hint_revealed" not in st.session_state:
    st.session_state.hint_revealed = False

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# -----------------------------
# 3. DASHBOARD
# -----------------------------
average_score = (
    round(st.session_state.total_score /
          st.session_state.attempts)
    if st.session_state.attempts > 0
    else 0
)

st.markdown("### 📊 Your progress")

col1, col2, col3 = st.columns(3)

col1.metric("Attempts", st.session_state.attempts)
col2.metric("Average score", f"{average_score}/100")
col3.metric("Hints used", st.session_state.hints_used)

st.divider()


# -----------------------------
# 4. DAILY CHALLENGE
# -----------------------------
st.markdown("### 🍕 Today's challenge: Pizza Estimation")

st.write(
    "Imagine 100 people are attending a party. "
    "Each person eats 3 slices of pizza. "
    "Each pizza contains 8 slices."
)

st.write(
    "**Question:** How many whole pizzas should "
    "the organizer order to feed everyone?"
)

# Hint button
if not st.session_state.hint_revealed:
    if st.button("💡 Reveal hint"):
        st.session_state.hint_revealed = True
        st.session_state.hints_used += 1
        st.rerun()

if st.session_state.hint_revealed:
    st.info(
        "First calculate the total number of slices. "
        "Then divide by 8. Remember to round UP because "
        "you cannot order a fraction of a whole pizza."
    )


# -----------------------------
# 5. GEMINI THINKING COACH
# -----------------------------

def get_ai_feedback(answer, reasoning, is_correct):
    """Ask Gemini to evaluate the player's reasoning."""

    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the Thinking Coach inside MindTrace,
a daily brain-game and reasoning-training app.

CHALLENGE:
100 people attend a party.
Each person eats 3 slices of pizza.
Each pizza contains 8 slices.

CORRECT ANSWER: 38 pizzas
PLAYER'S ANSWER: {answer}
IS THE NUMERICAL ANSWER CORRECT? {is_correct}
PLAYER'S EXPLANATION:
{reasoning if reasoning.strip() else "[No explanation provided]"}

Give helpful, concise feedback using these sections:

### 🧠 Your reasoning
Evaluate the explanation, not just the answer.
If no explanation was provided, say there is not enough information.

### ✅ What you did well
Identify a genuine strength supported by the explanation.

### 🎯 What to improve
Identify a mistake or missing step. If the method is sound,
explain how to make the explanation clearer.

### 💡 Your next thinking tip
Give one practical tip for another estimation problem.

The correct calculation is 100 x 3 = 300 slices.
300 / 8 = 37.5 pizzas, so round UP to 38 whole pizzas.

A correct answer alone does not prove sound reasoning.
A wrong answer can still show a good method.
Never claim to measure true IQ or diagnose personality.
"""

    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash"
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if response.text:
                return response.text

            last_error = ValueError(
                f"{model_name} returned an empty response."
            )

        except Exception as e:
            last_error = e

    raise RuntimeError(
        f"All model attempts failed. Last error: {last_error}"
    )




# -----------------------------
# 6. PLAYER ANSWER FORM
# -----------------------------
st.markdown("### ✍️ Show us how you think")

with st.form("answer_form"):
    player_answer = st.number_input(
        "How many whole pizzas would you order?",
        min_value=1,
        max_value=10000,
        value=38,
        step=1
    )

    reasoning = st.text_area(
        "Explain your reasoning",
        placeholder=(
            "For example: I calculated the total slices, "
            "then divided by the slices per pizza..."
        ),
        height=120
    )

    submitted = st.form_submit_button(
        "Submit answer & get AI feedback",
        type="primary",
        use_container_width=True
    )


# -----------------------------
# 7. CHECK ANSWER AND CALL AI
# -----------------------------
if submitted:
    correct_answer = 38
    difference = abs(int(player_answer) - correct_answer)

    if difference == 0:
        score = 100
    else:
        score = max(
            0,
            round(100 * (1 - difference / correct_answer))
        )

    is_correct = int(player_answer) == correct_answer

    # Update progress once for this submission.
    st.session_state.attempts += 1
    st.session_state.total_score += score

    # Save a result before calling the AI.
    # This prevents another API call on ordinary reruns.
    st.session_state.last_result = {
        "answer": int(player_answer),
        "reasoning": reasoning,
        "score": score,
        "is_correct": is_correct,
        "ai_feedback": None,
        "ai_error": False
    }

    try:
        feedback = get_ai_feedback(
            answer=int(player_answer),
            reasoning=reasoning,
            is_correct=is_correct
        )

        st.session_state.last_result["ai_feedback"] = feedback

    
    except Exception as e:
        st.session_state.last_result["ai_error"] = True
        st.session_state.last_result["ai_error_message"] = (
            f"{type(e).__name__}: {e}"
        )



# -----------------------------
# 8. DISPLAY LATEST RESULT
# -----------------------------
result = st.session_state.last_result

if result is not None:
    st.divider()
    st.markdown("## 📝 Your latest result")

    if result["is_correct"]:
        st.success("Correct! You calculated the number of pizzas.")
    else:
        st.warning(
            f"Not quite. Your answer was {result['answer']}; "
            "the correct answer is 38."
        )

    st.metric("Numerical accuracy score", f"{result['score']}/100")

    st.markdown("### 🤖 Your AI Thinking Coach")

    if result["ai_feedback"]:
        st.markdown(result["ai_feedback"])

    
    elif result["ai_error"]:
        st.error(
            "The answer was recorded, but the AI coach failed."
        )
        st.code(
            result.get(
                "ai_error_message",
                "No detailed error was captured."
            )
        )


    else:
        st.info("Submit an answer to receive your AI feedback.")

st.divider()

st.caption(
    "MindTrace is a reasoning practice tool. "
    "Its numerical score measures answer accuracy, "
    "not your IQ."
)
