
import time
import streamlit as st
import brain_twin_db as db
import plotly.graph_objects as go
from auth_ui import render_auth, clear_assessment_state
from google import genai
from assessment_logic import (
    category_summary as build_category_summary,
    next_difficulty,
    processing_speed_score,
)

# =========================================================
# 1. PAGE CONFIGURATION AND DESIGN
# =========================================================

st.set_page_config(
    page_title="MindTrace | Cognitive Assessment",
    page_icon="🧠",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top, #172554 0%, #090d1a 48%, #070912 100%);
    color: #eef2ff;
}
.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
h1, h2, h3 {
    color: #f1f5ff !important;
}
.mindtrace-subtitle {
    color: #a5b4fc;
    font-size: 1.05rem;
}
.category-label {
    display: inline-block;
    background: #1e1b4b;
    color: #a5b4fc;
    border: 1px solid #4f46e5;
    padding: 7px 13px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 1px;
}
.question-card {
    background: rgba(30, 41, 70, 0.70);
    border: 1px solid #34436c;
    border-radius: 18px;
    padding: 24px;
    margin: 16px 0;
}
div[data-testid="stMetric"] {
    background: rgba(30, 41, 70, 0.70);
    border: 1px solid #34436c;
    padding: 15px;
    border-radius: 14px;
}
div[data-testid="stMetricValue"] {
    color: #a5b4fc;
}
.stButton > button,
.stFormSubmitButton > button {
    border-radius: 12px;
    min-height: 44px;
    font-weight: 600;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    border: none;
    color: white;
}
hr {
    border-color: #293452;
}
</style>
""", unsafe_allow_html=True)
# Authentication gate: stop before showing the assessment.
if not render_auth():
    st.stop()

# =========================================================
# 2. QUESTION BANK: 36 QUESTIONS, SIX CATEGORIES
# =========================================================


questions = [
    # ==================================================
    # LOGIC & PATTERNS — 6 QUESTIONS
    # ==================================================
    {
        "category": "Logic & Patterns",
        "difficulty": "Moderate",
        "prompt": (
            "All Rens are Vaks. No Vaks are Tors. "
            "Some Mips are Rens. Which conclusion must be true?"
        ),
        "options": [
            "All Mips are Vaks",
            "Some Mips are not Tors",
            "No Mips are Tors",
            "Some Tors are Rens"
        ],
        "answer": "Some Mips are not Tors",
        "explanation": (
            "Some Mips are Rens, and every Ren is a Vak. "
            "No Vak is a Tor, so those Mips cannot be Tors."
        )
    },
    {
        "category": "Logic & Patterns",
        "difficulty": "Moderate",
        "prompt": (
            "A system follows this rule: if process P fails, "
            "the warning activates. The warning did not activate. "
            "Assuming the rule always holds, what follows?"
        ),
        "options": [
            "Process P failed",
            "Process P did not fail",
            "The warning is definitely broken",
            "Process P succeeded because another process failed"
        ],
        "answer": "Process P did not fail",
        "explanation": (
            "If P failed, the warning would activate. "
            "Since it did not activate, P did not fail."
        )
    },
    {
        "category": "Logic & Patterns",
        "difficulty": "Difficult",
        "prompt": (
            "Four tasks W, X, Y, and Z must be completed once each. "
            "W must happen before X. X must happen before Y. "
            "Z must happen before W. Which task must happen first?"
        ),
        "options": ["W", "X", "Y", "Z"],
        "answer": "Z",
        "explanation": (
            "The constraints establish the order Z before W, "
            "W before X, and X before Y. Therefore Z is first."
        )
    },
    {
        "category": "Logic & Patterns",
        "difficulty": "Difficult",
        "prompt": (
            "Find the next number: 2, 5, 10, 17, 26, ?"
        ),
        "options": ["35", "36", "37", "38"],
        "answer": "37",
        "explanation": (
            "The differences are 3, 5, 7, and 9. "
            "The next difference is 11, giving 26 + 11 = 37."
        )
    },
    {
        "category": "Logic & Patterns",
        "difficulty": "Challenging",
        "prompt": (
            "A code transforms each letter into the letter "
            "two places later in the alphabet, wrapping around "
            "after Z. For example, X becomes Z. How is LAMP encoded?"
        ),
        "options": ["NCOR", "NCOQ", "MBOQ", "OCPS"],
        "answer": "NCOR",
        "explanation": (
            "L→N, A→C, M→O, and P→R. "
            "Applying the same rule gives NCOR."
        )
    },
    {
        "category": "Logic & Patterns",
        "difficulty": "Challenging",
        "prompt": (
            "Four cards show A, K, 4, and 7. Each card has a "
            "letter on one side and a number on the other. "
            "Rule: if a card has a vowel on one side, it must "
            "have an even number on the other. Which cards must "
            "you turn over to test whether the rule is violated?"
        ),
        "options": [
            "A and 4",
            "A and 7",
            "K and 4",
            "K and 7"
        ],
        "answer": "A and 7",
        "explanation": (
            "Turn A to check for an even number. Turn 7 to check "
            "that its other side is not a vowel. K and 4 cannot "
            "falsify the rule."
        )
    },

    # ==================================================
    # NUMERICAL REASONING — 6 QUESTIONS
    # ==================================================
    {
        "category": "Numerical Reasoning",
        "difficulty": "Moderate",
        "prompt": (
            "What number comes next? 2, 6, 15, 31, 56, ?"
        ),
        "options": ["82", "91", "92", "96"],
        "answer": "92",
        "explanation": (
            "The differences are 4, 9, 16, and 25, which are "
            "squares of 2, 3, 4, and 5. Add 6² = 36 to 56."
        )
    },
    {
        "category": "Numerical Reasoning",
        "difficulty": "Moderate",
        "prompt": (
            "A product costs 250 dinars. Its price increases "
            "by 20%, then the new price decreases by 20%. "
            "What is the final price?"
        ),
        "options": ["240 dinars", "250 dinars",
                    "260 dinars", "200 dinars"],
        "answer": "240 dinars",
        "explanation": (
            "250 × 1.20 = 300. Then 300 × 0.80 = 240. "
            "The two percentage changes apply to different bases."
        )
    },
    {
        "category": "Numerical Reasoning",
        "difficulty": "Difficult",
        "prompt": (
            "Two quantities are in the ratio 4:7. Their difference "
            "is 24. What is the larger quantity?"
        ),
        "options": ["32", "48", "56", "72"],
        "answer": "56",
        "explanation": (
            "The difference is 7 − 4 = 3 parts. "
            "Each part is 24 ÷ 3 = 8. The larger quantity is 7 × 8 = 56."
        )
    },
    {
        "category": "Numerical Reasoning",
        "difficulty": "Difficult",
        "prompt": (
            "Four identical printers produce 240 pages in "
            "6 minutes, working at a constant rate. How many "
            "pages can three such printers produce in 15 minutes?"
        ),
        "options": ["300", "360", "450", "600"],
        "answer": "450",
        "explanation": (
            "Each printer produces 240 ÷ (4 × 6) = 10 pages "
            "per minute. Three printers produce 3 × 10 × 15 = 450."
        )
    },
    {
        "category": "Numerical Reasoning",
        "difficulty": "Challenging",
        "prompt": (
            "The mean of five numbers is 18. One number, 30, "
            "is removed. What is the mean of the four remaining numbers?"
        ),
        "options": ["12", "15", "16", "18"],
        "answer": "15",
        "explanation": (
            "The original total is 5 × 18 = 90. After removing 30, "
            "the total is 60. The new mean is 60 ÷ 4 = 15."
        )
    },
    {
        "category": "Numerical Reasoning",
        "difficulty": "Challenging",
        "prompt": (
            "A bag contains 4 red, 3 blue, and 2 green balls. "
            "Two balls are drawn without replacement. What is the "
            "probability that both are red?"
        ),
        "options": ["1/6", "2/9", "1/3", "4/9"],
        "answer": "1/6",
        "explanation": (
            "The probability is (4/9) × (3/8) = 12/72 = 1/6. "
            "The second draw has only three red balls among eight total."
        )
    },

    # ==================================================
    # SPATIAL REASONING — 6 QUESTIONS
    # ==================================================
    {
        "category": "Spatial Reasoning",
        "difficulty": "Moderate",
        "prompt": (
            "A point is at coordinates (3, -2). Rotate the point "
            "90 degrees counterclockwise around the origin. "
            "What are its new coordinates?"
        ),
        "options": ["(-2, -3)", "(2, 3)", "(-3, 2)", "(2, -3)"],
        "answer": "(2, 3)",
        "explanation": (
            "A 90-degree counterclockwise rotation maps (x, y) "
            "to (-y, x). Therefore (3, -2) becomes (2, 3)."
        )
    },
    {
        "category": "Spatial Reasoning",
        "difficulty": "Moderate",
        "prompt": (
            "Complete the 4 × 4 pattern:\n\n"
            "○  △  □  ◇\n"
            "△  □  ◇  ○\n"
            "□  ◇  ○  △\n"
            "◇  ○  △  ?"
        ),
        "options": ["○", "△", "□", "◇"],
        "answer": "□",
        "explanation": (
            "Each row shifts the previous row one position to the "
            "left, wrapping the first symbol to the end. The missing "
            "symbol is a square."
        )
    },
    {
        "category": "Spatial Reasoning",
        "difficulty": "Difficult",
        "prompt": (
            "A large cube is painted on all six outer faces, then "
            "cut into 27 identical smaller cubes (3 × 3 × 3). "
            "How many small cubes have exactly two painted faces?"
        ),
        "options": ["8", "12", "18", "24"],
        "answer": "12",
        "explanation": (
            "Cubes with exactly two painted faces lie along the "
            "edges, excluding the corners. Each of 12 edges has "
            "one such cube in a 3 × 3 × 3 division."
        )
    },
    {
        "category": "Spatial Reasoning",
        "difficulty": "Difficult",
        "prompt": (
            "You face north. You turn 90 degrees clockwise, "
            "then 180 degrees, then 90 degrees counterclockwise. "
            "Which direction are you facing now?"
        ),
        "options": ["North", "East", "South", "West"],
        "answer": "South",
        "explanation": (
            "North → East → West → South. The final direction is south."
        )
    },
    {
        "category": "Spatial Reasoning",
        "difficulty": "Challenging",
        "prompt": (
            "A point at (−2, 5) is reflected across the vertical "
            "y-axis, then across the horizontal x-axis. "
            "Where does it end up?"
        ),
        "options": ["(2, −5)", "(−2, −5)", "(5, −2)", "(2, 5)"],
        "answer": "(2, −5)",
        "explanation": (
            "Reflection across the y-axis changes x: (−2, 5) → "
            "(2, 5). Reflection across the x-axis changes y: "
            "(2, 5) → (2, −5)."
        )
    },
    {
        "category": "Spatial Reasoning",
        "difficulty": "Challenging",
        "prompt": (
            "A cube is painted on all outer faces and cut into "
            "64 equal smaller cubes (4 × 4 × 4). How many small "
            "cubes have exactly one painted face?"
        ),
        "options": ["8", "16", "24", "32"],
        "answer": "24",
        "explanation": (
            "On each face, the cubes with exactly one painted face "
            "are the interior face cubes: (4 − 2)² = 4 per face. "
            "Across six faces, 6 × 4 = 24."
        )
    },

    # ==================================================
    # WORKING MEMORY — 6 QUESTIONS
    # The sequence is shown first and hidden before answering.
    # ==================================================
    {
        "category": "Working Memory",
        "difficulty": "Moderate",
        "sequence": "5 – 2 – 8 – 1",
        "prompt": (
            "After the sequence disappears, select the same "
            "numbers in reverse order."
        ),
        "options": [
            "1 – 8 – 2 – 5",
            "1 – 2 – 8 – 5",
            "5 – 8 – 2 – 1",
            "8 – 1 – 2 – 5"
        ],
        "answer": "1 – 8 – 2 – 5",
        "explanation": (
            "Reversing 5 – 2 – 8 – 1 gives 1 – 8 – 2 – 5."
        )
    },
    {
        "category": "Working Memory",
        "difficulty": "Moderate",
        "sequence": "8 – 3 – 6 – 1 – 5",
        "prompt": (
            "After the sequence disappears, select its digits "
            "arranged from smallest to largest."
        ),
        "options": [
            "1 – 3 – 5 – 6 – 8",
            "1 – 3 – 6 – 5 – 8",
            "8 – 6 – 5 – 3 – 1",
            "3 – 1 – 5 – 6 – 8"
        ],
        "answer": "1 – 3 – 5 – 6 – 8",
        "explanation": (
            "Sorting the remembered digits in ascending order "
            "gives 1, 3, 5, 6, 8."
        )
    },
    {
        "category": "Working Memory",
        "difficulty": "Difficult",
        "sequence": "6 – 2 – 9 – 4 – 7 – 1",
        "prompt": (
            "After the sequence disappears, what is the sum "
            "of the second and fifth numbers?"
        ),
        "options": ["8", "9", "11", "13"],
        "answer": "9",
        "explanation": (
            "The second number is 2 and the fifth is 7. "
            "Their sum is 2 + 7 = 9."
        )
    },
    {
        "category": "Working Memory",
        "difficulty": "Difficult",
        "sequence": "K – 4 – M – 9 – B – 2",
        "prompt": (
            "After the sequence disappears, which two symbols "
            "were immediately before and after M, respectively?"
        ),
        "options": [
            "4 and 9",
            "K and 9",
            "4 and B",
            "9 and B"
        ],
        "answer": "4 and 9",
        "explanation": (
            "In K – 4 – M – 9 – B – 2, the symbol before M is 4 "
            "and the symbol after M is 9."
        )
    },
    {
        "category": "Working Memory",
        "difficulty": "Challenging",
        "sequence": "3 – 8 – 1 – 6 – 4 – 9 – 2",
        "prompt": (
            "After the sequence disappears, select its numbers "
            "in reverse order, then add the first and last "
            "numbers of that reversed sequence."
        ),
        "options": ["5", "6", "11", "12"],
        "answer": "5",
        "explanation": (
            "The reversed sequence is 2 – 9 – 4 – 6 – 1 – 8 – 3. "
            "Its first and last numbers are 2 and 3; their sum is 5."
        )
    },
    {
        "category": "Working Memory",
        "difficulty": "Challenging",
        "sequence": "D – 3 – A – 8 – F – 2",
        "prompt": (
            "After the sequence disappears, keep the letters in "
            "alphabetical order, followed by the numbers in "
            "ascending order."
        ),
        "options": [
            "A – D – F – 2 – 3 – 8",
            "D – A – F – 2 – 3 – 8",
            "A – D – F – 8 – 3 – 2",
            "2 – 3 – 8 – A – D – F"
        ],
        "answer": "A – D – F – 2 – 3 – 8",
        "explanation": (
            "The letters in alphabetical order are A, D, F. "
            "The digits in ascending order are 2, 3, 8."
        )
    },

    # ==================================================
    # PROCESSING SPEED — 6 QUESTIONS
    # IMPORTANT: a real timer must be implemented separately.
    # ==================================================
    {
        "category": "Processing Speed",
        "difficulty": "Moderate",
        "prompt": (
            "Compare the two codes. Are they exactly identical?\n\n"
            "R8K2M7  |  R8K2M7"
        ),
        "options": ["Identical", "Different"],
        "answer": "Identical",
        "explanation": (
            "All six characters match in the same order."
        )
    },
    {
        "category": "Processing Speed",
        "difficulty": "Moderate",
        "prompt": (
            "Which character differs between these codes?\n\n"
            "P6Q8R2  |  P6O8R2"
        ),
        "options": ["P", "6", "Q / O", "R"],
        "answer": "Q / O",
        "explanation": (
            "The third character is Q in the first code and O "
            "in the second."
        )
    },
    {
        "category": "Processing Speed",
        "difficulty": "Difficult",
        "prompt": (
            "How many times does the exact sequence 'AB' occur "
            "in this string?\n\n"
            "ABBAABABBAAB"
        ),
        "options": ["2", "3", "4", "5"],
        "answer": "4",
        "explanation": (
            "The sequence AB starts at positions 1, 5, 7, and 11. "
            "There are four occurrences."
        )
    },
    {
        "category": "Processing Speed",
        "difficulty": "Difficult",
        "prompt": (
            "Which option contains the characters in exactly "
            "the same order as the target?\n\n"
            "Target:  7B2Q9M4"
        ),
        "options": [
            "7B2Q9N4",
            "7B2Q9M4",
            "7B2O9M4",
            "7B2Q4M9"
        ],
        "answer": "7B2Q9M4",
        "explanation": (
            "Only the second option matches every character "
            "at every position."
        )
    },
    {
        "category": "Processing Speed",
        "difficulty": "Challenging",
        "prompt": (
            "Count the exact matches between the target and the "
            "four codes below. How many codes match completely?\n\n"
            "Target:  K4M8P2\n"
            "1) K4M8P2\n"
            "2) K4N8P2\n"
            "3) K4M8P2\n"
            "4) K4M8PZ"
        ),
        "options": ["1", "2", "3", "4"],
        "answer": "2",
        "explanation": (
            "Codes 1 and 3 match the target exactly. Codes 2 and 4 "
            "each contain one different character."
        )
    },
    {
        "category": "Processing Speed",
        "difficulty": "Challenging",
        "prompt": (
            "Starting from the left, compare the two strings. "
            "At which position is the first mismatch?\n\n"
            "String A:  T8K3M6Q2\n"
            "String B:  T8K3N6Q2"
        ),
        "options": [
            "Position 3",
            "Position 4",
            "Position 5",
            "Position 6"
        ],
        "answer": "Position 5",
        "explanation": (
            "Positions 1–4 match. At position 5, A has M and B has N."
        )
    },

    # ==================================================
    # VERBAL REASONING — 6 QUESTIONS
    # ==================================================
    {
        "category": "Verbal Reasoning",
        "difficulty": "Moderate",
        "prompt": (
            "Scalpel is to surgeon as chisel is to ..."
        ),
        "options": ["Sculptor", "Pilot", "Judge", "Librarian"],
        "answer": "Sculptor",
        "explanation": (
            "A scalpel is a tool used by a surgeon; a chisel is "
            "a tool commonly used by a sculptor."
        )
    },
    {
        "category": "Verbal Reasoning",
        "difficulty": "Moderate",
        "prompt": (
            "Which word is closest in meaning to 'meticulous'?"
        ),
        "options": ["Careless", "Thorough", "Impulsive", "Vague"],
        "answer": "Thorough",
        "explanation": (
            "Meticulous describes someone who pays careful "
            "attention to details."
        )
    },
    {
        "category": "Verbal Reasoning",
        "difficulty": "Difficult",
        "prompt": (
            "Every approved report has a reference number. "
            "Some archived documents are approved reports. "
            "Which conclusion must be true?"
        ),
        "options": [
            "Every archived document has a reference number",
            "Some archived documents have a reference number",
            "No archived document has a reference number",
            "Every document with a reference number is archived"
        ],
        "answer": "Some archived documents have a reference number",
        "explanation": (
            "Some archived documents are approved reports, and "
            "every approved report has a reference number. "
            "Those archived documents therefore have reference numbers."
        )
    },
    {
        "category": "Verbal Reasoning",
        "difficulty": "Difficult",
        "prompt": (
            "A statement says: 'Although the prototype was cheaper "
            "to build, it required more maintenance than the original.' "
            "Which conclusion is best supported?"
        ),
        "options": [
            "The prototype was cheaper overall",
            "The prototype required less maintenance",
            "The prototype had a lower initial cost but a greater "
            "maintenance burden",
            "The original was more expensive to maintain"
        ],
        "answer": (
            "The prototype had a lower initial cost but a greater "
            "maintenance burden"
        ),
        "explanation": (
            "The statement compares initial construction cost with "
            "maintenance needs. It does not establish total lifetime cost."
        )
    },
    {
        "category": "Verbal Reasoning",
        "difficulty": "Challenging",
        "prompt": (
            "A researcher concludes that a new study method improves "
            "exam results because students who chose the method scored "
            "higher than students who did not. Which fact most weakens "
            "the conclusion?"
        ),
        "options": [
            "The study method takes 20 minutes to learn",
            "Students chose their own method, and the students who "
            "chose the new method already had higher previous grades",
            "The exam contained 40 questions",
            "Some students preferred studying in the morning"
        ],
        "answer": (
            "Students chose their own method, and the students who "
            "chose the new method already had higher previous grades"
        ),
        "explanation": (
            "Pre-existing differences could explain the higher scores. "
            "The comparison alone does not establish that the method "
            "caused the improvement."
        )
    },
    {
        "category": "Verbal Reasoning",
        "difficulty": "Challenging",
        "prompt": (
            "Consider these statements:\n"
            "1. No encrypted file can be read without the correct key.\n"
            "2. File X was read without the correct key.\n"
            "Assuming statement 1 is always true, what must follow?"
        ),
        "options": [
            "File X was encrypted",
            "File X was not encrypted",
            "File X was definitely corrupted",
            "The key was correct after all"
        ],
        "answer": "File X was not encrypted",
        "explanation": (
            "If an encrypted file cannot be read without the correct "
            "key, a file read without that key cannot be encrypted, "
            "assuming the rule and the facts are accurate."
        )
    }
]



# =========================================================

# =========================================================
# 3. SESSION STATE
# =========================================================

categories = [
    "Logic & Patterns",
    "Numerical Reasoning",
    "Spatial Reasoning",
    "Working Memory",
    "Processing Speed",
    "Verbal Reasoning",
]


def build_fallback_report(
    category_summary,
    cognitive_index,
    correct_count,
    total_questions,
    average_seconds,
    previous_attempts,
):
    """Build a rule-based coaching report when Gemini is unavailable."""
    ranked = sorted(
        (
            category,
            details.get("score", 0),
        )
        for category, details in category_summary.items()
        if details.get("total", 0) > 0
    )

    if ranked:
        strongest_category, strongest_score = max(
            ranked,
            key=lambda item: item[1],
        )
        weakest_category, weakest_score = min(
            ranked,
            key=lambda item: item[1],
        )
    else:
        strongest_category, strongest_score = "No category", 0
        weakest_category, weakest_score = "No category", 0

    exercise_suggestions = {
        "Logic & Patterns": "Solve one short sequencing or rule-checking puzzle.",
        "Numerical Reasoning": "Work through five estimation or number-pattern problems.",
        "Spatial Reasoning": "Rotate or compare five simple shapes before checking answers.",
        "Working Memory": "Recall a short list after a one-minute distraction.",
        "Processing Speed": "Complete a timed set of easy comparisons while keeping accuracy steady.",
        "Verbal Reasoning": "Summarize a short argument and identify its conclusion.",
    }

    weak_categories = [
        category
        for category, score in sorted(ranked, key=lambda item: item[1])[:3]
    ]
    exercises = "\n".join(
        f"- {category}: {exercise_suggestions.get(category, 'Practice a short set of related questions.')}"
        for category in weak_categories
    )

    if previous_attempts:
        previous_score = previous_attempts[-1].get("cognitive_index", 0)
        progress = (
            f"The previous recorded Cognitive Index was {previous_score}/100; "
            f"the current result is {cognitive_index}/100."
        )
    else:
        progress = "This is the baseline; future assessments can help track change."

    return f"""## 1. Overall performance
You answered {correct_count} of {total_questions} questions correctly, for a Cognitive Index of {cognitive_index}/100. Average response time was {average_seconds:.1f} seconds. This experimental profile is not standardized.

## 2. Cognitive strengths
Your highest current category was {strongest_category} at {strongest_score}%.

## 3. Areas to practise
The category with the most room for practice was {weakest_category} at {weakest_score}%. This is a practice opportunity, not a permanent label.

## 4. Progress over time
{progress} A score change does not by itself establish lasting improvement.

## 5. Three targeted exercises
{exercises or '- Complete a short mixed practice set covering three categories.'}

## 6. Next practice plan
Choose one exercise above and complete one focused 10-minute session, keeping accuracy and response time in view.

## 7. Motivational closing
Use this snapshot as a guide for your next practice session. Small, consistent repetitions can make your progress easier to observe.

*Report generated without AI (service unavailable).*"""

defaults = {
    "current_index": 0,
    "answers": {},
    "memory_ready": False,
    "question_started_at": time.time(),
    "ai_report": None,
    "ai_report_error": None,
    "skill_difficulty": {category: "Moderate" for category in categories},
    "skill_stats": {},
    "question_order": [],
    "seen_questions": [],
    "category_schedule": categories * 6,
    "assessment_length": 36,
    "assessment_started": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 4. HEADER
# =========================================================

st.markdown("# 🧠 MindTrace")
st.markdown(
    '<p class="mindtrace-subtitle">'
    'THINK DIFFERENTLY. DISCOVER YOUR STRENGTHS.'
    '</p>',
    unsafe_allow_html=True
)

st.write(
    "A multi-skill cognitive challenge combining logic, "
    "numbers, spatial reasoning, memory, speed, and language."
)
st.caption("Prototype assessment · Not a clinically validated IQ test")
st.caption("No biometric data (camera, voice, or face) is collected.")
st.divider()


# =========================================================
# 5. ASSESSMENT SCREEN
# =========================================================


# Let the user choose an assessment length before starting.
if not st.session_state.assessment_started:
    st.divider()
    st.subheader("🎯 Choose your assessment")
    st.write("How much time would you like to spend training today?")

    selected_length = st.selectbox(
        "Assessment length",
        options=[12, 24, 36],
        format_func=lambda n: {
            12: "12 questions — Quick Check",
            24: "24 questions — Standard Assessment",
            36: "36 questions — Full Assessment",
        }[n],
        index=2,
        key="assessment_length_selector",
    )

    st.caption(
        "Every assessment covers all six cognitive categories. "
        "Shorter assessments provide a quicker snapshot."
    )

    if st.button(
    "Start my assessment 🚀",
    type="primary",
    use_container_width=True,
):
    # Start a completely fresh assessment.
        st.session_state.current_index = 0
        st.session_state.answers = {}
        st.session_state.memory_ready = False
        st.session_state.question_started_at = time.time()
        st.session_state.ai_report = None
        st.session_state.ai_report_error = None
        st.session_state.question_order = []
        st.session_state.seen_questions = []
        st.session_state.skill_difficulty = {
            category: "Moderate" for category in categories
        }
        st.session_state.skill_stats = {}
        st.session_state.assessment_length = selected_length
        st.session_state.assessment_started = True
        st.session_state.pop("assessment_saved_run_id", None)
        st.rerun()

    st.stop()

total_questions = st.session_state.assessment_length
current_index = st.session_state.current_index


if current_index < total_questions:

    # Choose an unused question for the scheduled category.
    if len(st.session_state.question_order) <= current_index:
        category = st.session_state.category_schedule[current_index]

        candidates = [
            (index, q)
            for index, q in enumerate(questions)
            if q["category"] == category
            and index not in st.session_state.seen_questions
        ]

        difficulty_rank = {
            "Moderate": 0,
            "Difficult": 1,
            "Challenging": 2,
        }

        target = st.session_state.skill_difficulty[category]

        candidates.sort(
            key=lambda item: abs(
                difficulty_rank[item[1]["difficulty"]]
                - difficulty_rank[target]
            )
        )

        if not candidates:
            st.error("No unused questions remain for this skill.")
            st.stop()

        selected_index = candidates[0][0]
        st.session_state.question_order.append(selected_index)
        st.session_state.seen_questions.append(selected_index)

    question_index = st.session_state.question_order[current_index]
    question = questions[question_index]

    st.progress(current_index / total_questions)

    col1, col2 = st.columns(2)
    col1.metric("Question", f"{current_index + 1} / {total_questions}")
    col2.metric("Answered", len(st.session_state.answers))

    st.markdown(
        f'<span class="category-label">'
        f'{question["category"].upper()}'
        f'</span>',
        unsafe_allow_html=True
    )

    st.markdown("")

    # Working-memory study phase.
    if question.get("sequence") and not st.session_state.memory_ready:
        st.markdown("## Memorize this sequence")
        st.write(
            "Study the sequence carefully. Press the button when ready. "
            "The sequence will disappear before you answer."
        )

        st.markdown(
            f'<div class="question-card" '
            f'style="text-align:center;font-size:2rem;'
            f'letter-spacing:5px;color:#a5b4fc;">'
            f'{question["sequence"]}</div>',
            unsafe_allow_html=True
        )

        if st.button(
            "I've memorized it — hide the sequence",
            type="primary",
            use_container_width=True
        ):
            st.session_state.memory_ready = True
            st.session_state.question_started_at = time.time()
            st.rerun()

    else:
        st.markdown(
            f'<div class="question-card">'
            f'<h3>Challenge {current_index + 1}</h3>'
            f'<p style="font-size:1.15rem;">'
            f'{question["prompt"]}</p></div>',
            unsafe_allow_html=True
        )

        st.caption(f"Difficulty: {question['difficulty']}")

        if current_index == 0:
            st.info(
                "Choose the best answer. Your results will appear "
                "after you complete all 36 questions."
            )

        with st.form(f"question_form_{current_index}"):
            selected = st.radio(
                "Choose one answer",
                question["options"],
                index=None,
                key=f"choice_{current_index}"
            )

            submitted = st.form_submit_button(
                "Submit and continue →",
                type="primary",
                use_container_width=True
            )

        if submitted:
            if selected is None:
                st.warning("Choose an answer before continuing.")
            else:
                elapsed = max(
                    0.0,
                    time.time() - st.session_state.question_started_at
                )

                category = question["category"]
                is_correct = selected == question["answer"]

                st.session_state.answers[current_index] = {
                    "category": category,
                    "difficulty": question["difficulty"],
                    "question": question["prompt"],
                    "chosen": selected,
                    "correct": question["answer"],
                    "is_correct": is_correct,
                    "seconds": round(elapsed, 2),
                    "explanation": question["explanation"],
                }

                stats = st.session_state.skill_stats.setdefault(
                    category, {"correct": 0, "answered": 0}
                )
                stats["answered"] += 1

                if is_correct:
                    stats["correct"] += 1

                st.session_state.skill_difficulty[category] = next_difficulty(
                    st.session_state.skill_difficulty[category],
                    is_correct,
                )

                st.session_state.current_index += 1
                st.session_state.memory_ready = False
                st.session_state.question_started_at = time.time()
                st.rerun()


# =========================================================
# 6. FINAL RESULTS
# =========================================================

else:
    st.balloons()
    st.markdown("## ✨ Your MindTrace Results")
    st.write(
        "You've completed the assessment. Here is your performance "
        "across the six categories."
    )

    answers = list(st.session_state.answers.values())
    correct_count = sum(a["is_correct"] for a in answers)

    cognitive_index = round(
        100 * correct_count / total_questions
    )

    average_seconds = (
        sum(a["seconds"] for a in answers) / len(answers)
        if answers else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Cognitive Index", f"{cognitive_index}/100")
    col2.metric("Correct answers", f"{correct_count}/{total_questions}")
    col3.metric("Avg. response time", f"{average_seconds:.1f}s")

    st.progress(cognitive_index / 100)

    st.caption(
        "This index is the percentage of correct answers in this "
        "prototype. It is not an IQ score or a validated measure "
        "of intelligence."
    )

    st.divider()
    st.markdown("### 📊 Performance by category")

    category_summary = build_category_summary(answers, categories)

    processing_speed = category_summary["Processing Speed"]
    if processing_speed["total"]:
        processing_speed["accuracy_score"] = processing_speed["score"]
        processing_speed["score"] = processing_speed_score(
            processing_speed["correct"],
            processing_speed["total"],
            processing_speed["average_seconds"],
        )

    for category in categories:
        details = category_summary[category]
        category_correct = details["correct"]
        category_total = details["total"]
        category_score = details["score"]
        interval_low = details["interval_low"]
        interval_high = details["interval_high"]

        if category == "Processing Speed" and category_total:
            score_label = (
                f"{category_score}% combined score "
                "(70% accuracy + 30% rapidness)"
            )
        else:
            score_label = f"{category_score}%"

        st.write(
            f"**{category}** — {category_correct}/{category_total} "
            f"correct ({score_label} | 95% CI: "
            f"{interval_low}-{interval_high}%)"
        )
        st.progress(category_score / 100)

    category_time = (
        sum(answer["seconds"] for answer in answers) / len(answers)
        if answers else 0
    )
        
    st.caption(
        f"Average response time: {category_time:.1f} seconds per question. "
        "With few questions per category, uncertainty is high; this "
        "profile is not a standardized measure."
    )

    st.divider()
    st.markdown("### 🧠 Your Cognitive Fingerprint")
    st.write(
        "A visual snapshot of your performance across the six "
        "cognitive dimensions."
    )

    profile_data = {
        category: details["score"]
        for category, details in category_summary.items()
        if details["total"] > 0
    }

    if profile_data:
        labels = list(profile_data.keys())
        scores = list(profile_data.values())
        interval_lows = [
            category_summary[category].get("interval_low", 0)
            for category in labels
        ]
        interval_highs = [
            category_summary[category].get("interval_high", 100)
            for category in labels
        ]

        # Close the radar shape by repeating the first dimension.
        radar_labels = labels + [labels[0]]
        radar_scores = scores + [scores[0]]
        radar_lows = interval_lows + [interval_lows[0]]
        radar_highs = interval_highs + [interval_highs[0]]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=radar_scores,
                theta=radar_labels,
                fill="toself",
                name="Your performance",
                line=dict(color="#8B5CF6", width=3),
                fillcolor="rgba(139, 92, 246, 0.22)",
                marker=dict(
                    size=8,
                    color="#38BDF8",
                    line=dict(color="#FFFFFF", width=1),
                ),
                hovertemplate=(
                    "<b>%{theta}</b><br>"
                    "Accuracy: %{r}%"
                    "<extra></extra>"
                ),
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=radar_lows,
                theta=radar_labels,
                name="95% CI lower bound",
                line=dict(color="#38BDF8", width=1, dash="dot"),
                hovertemplate=(
                    "<b>%{theta}</b><br>"
                    "Lower bound: %{r}%"
                    "<extra></extra>"
                ),
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=radar_highs,
                theta=radar_labels,
                name="95% CI upper bound",
                line=dict(color="#FBBF24", width=1, dash="dot"),
                hovertemplate=(
                    "<b>%{theta}</b><br>"
                    "Upper bound: %{r}%"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            height=480,
            margin=dict(l=55, r=55, t=35, b=35),
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[0, 25, 50, 75, 100],
                    ticksuffix="%",
                    gridcolor="rgba(148,163,184,0.25)",
                    linecolor="rgba(148,163,184,0.25)",
                ),
                angularaxis=dict(
                    gridcolor="rgba(148,163,184,0.25)",
                    linecolor="rgba(148,163,184,0.25)",
                    tickfont=dict(size=11, color="#E2E8F0"),
                ),
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.caption(
            "Each axis represents accuracy in one category. "
            "A larger value means more correct answers in that "
            "category, not a standardized measure of ability."
        )

        st.divider()
        st.markdown("### 🎯 Your performance highlights")

        ranked = sorted(
            profile_data.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        best_category, best_score = ranked[0]
        lowest_category, lowest_score = ranked[-1]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💪 Strongest result")
            st.metric(best_category, f"{best_score}% accuracy")

        with col2:
            st.markdown("#### 🚀 Opportunity to improve")
            st.metric(lowest_category, f"{lowest_score}% accuracy")

        if len(ranked) == 1:
            st.info(
                "Complete more categories to build a useful "
                "performance profile."
            )

    
    # Save this completed assessment only once.
    if not st.session_state.get("assessment_saved_run_id"):
        try:
            run_id = db.save_assessment(
                user_id=st.session_state["user_id"],
                cognitive_index=cognitive_index,
                correct_count=correct_count,
                total_questions=total_questions,
                average_seconds=average_seconds,
                category_scores=category_summary,
            )

            st.session_state["assessment_saved_run_id"] = run_id
            st.success("Your results have been saved to your Brain Twin.")

        except Exception:
            st.error(
                "Your results could not be saved. "
                "Your current results are still visible. "
                "Please report this issue before starting another assessment."
            )

    st.divider()
    st.markdown("## 🤖 Your AI Thinking Coach")
    st.write(
        "Generate a personalized report based on your recorded answers."
    )

    if st.session_state.ai_report is None:
        if st.button(
            "Generate my AI coaching report ✨",
            type="primary",
            use_container_width=True
        ):
            report_data = []

            for category, data in category_summary.items():
                report_data.append(
                    f"{category}: {data['correct']}/{data['total']} "
                    f"correct, {data['score']}%, average response "
                    f"time {data['average_seconds']} seconds."
                )

            missed_details = []

            for item in answers:
                if not item["is_correct"]:
                    missed_details.append(
                        f"Category: {item['category']}; "
                        f"Question: {item['question']}; "
                        f"Selected: {item['chosen']}; "
                        f"Correct answer: {item['correct']}; "
                        f"Explanation: {item['explanation']}"
                    )

            
            # Retrieve only this signed-in user's saved history.
            try:
                history = db.get_user_history(
                    st.session_state["user_id"]
                )
            except Exception:
                history = []

            current_run_id = st.session_state.get(
                "assessment_saved_run_id"
            )
            if current_run_id:
                previous_attempts = [
                    attempt for attempt in history
                    if attempt.get("run_id") != current_run_id
                ]
            else:
                previous_attempts = history

            history_lines = []

            for attempt_number, attempt in enumerate(
                previous_attempts[-5:], start=1
            ):
                history_lines.append(
                    f"Previous attempt: "
                    f"Cognitive Index {attempt['cognitive_index']}/100; "
                    f"correct {attempt['correct_count']}/"
                    f"{attempt['total_questions']}; "
                    f"average response time "
                    f"{attempt['average_seconds']:.2f} seconds."
                )

                previous_categories = attempt.get(
                    "category_scores", {}
                )

                for category, details in previous_categories.items():
                    history_lines.append(
                        f"  {category}: "
                        f"{details.get('score', 0)}%, "
                        f"{details.get('correct', 0)}/"
                        f"{details.get('total', 0)} correct."
                    )

            history_context = (
                "\n".join(history_lines)
                if history_lines
                else (
                    "No previous assessment records are available. "
                    "Treat this as the user's baseline."
                )
            )

            prompt = f"""
You are the MindTrace Thinking Coach, a careful and supportive
cognitive-practice assistant.

Analyze the user's current experimental reasoning assessment.
Use the current results and historical data supplied below.

CURRENT ASSESSMENT
Cognitive Index: {cognitive_index}/100
Correct answers: {correct_count}/{total_questions}
Average response time: {average_seconds:.2f} seconds.

CURRENT CATEGORY RESULTS
{chr(10).join(report_data)}

INCORRECT ANSWERS
{chr(10).join(missed_details) if missed_details else "No incorrect answers."}

PREVIOUS ASSESSMENTS
{history_context}

Write a personalized report with these sections:

1. Overall performance
Summarize the current assessment using its actual results.

2. Cognitive strengths
Identify stronger categories using current category scores.

3. Areas to practise
Identify categories with lower scores. Explain this as a practice
opportunity, not a permanent weakness.

4. Progress over time
If previous assessments are available, compare the current results
with previous results. Mention concrete score changes only when
supported by the supplied data. Discuss category-level changes only
when comparable category scores exist.
If there is no previous assessment, explain that this is the baseline
and future assessments can help track progress.
Do not claim that a score change proves a lasting improvement.

5. Three targeted exercises
Recommend practical exercises connected to the user's actual results.
Explain briefly which skill each exercise targets.

6. Next practice plan
Give the user one manageable goal for their next practice session.

7. Motivational closing
Keep it encouraging, realistic, and specific.

RULES
- Use only the supplied assessment results and history.
- Never invent scores, trends, or personal characteristics.
- Do not diagnose conditions or use clinical labels.
- Do not describe the Cognitive Index as a validated IQ score.
- State that MindTrace is experimental and non-standardized.
- Be concise, supportive, and practical.
- Historical records may be incomplete; acknowledge missing data
  instead of guessing.
"""


            try:
                with st.spinner("Your Thinking Coach is working..."):
                    api_key = st.secrets["GEMINI_API_KEY"]
                    client = genai.Client(api_key=api_key)

                    models_to_try = [
                        "gemini-3.6-flash",
                        "gemini-3.5-flash-lite",
                        "gemini-3.8-flash",
                    ]

                    report = None
                    last_error = None

                    for model_name in models_to_try:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=prompt
                            )

                            if response.text:
                                report = response.text
                                break

                            last_error = ValueError(
                                f"{model_name} returned an empty response."
                            )
                        except Exception as error:
                            last_error = error

                    if report:
                        st.session_state.ai_report = report
                        st.session_state.ai_report_error = None
                    else:
                        raise RuntimeError(
                            f"All model attempts failed. Last error: "
                            f"{last_error}"
                        )

            except Exception as error:
                st.session_state.ai_report = build_fallback_report(
                    category_summary=category_summary,
                    cognitive_index=cognitive_index,
                    correct_count=correct_count,
                    total_questions=total_questions,
                    average_seconds=average_seconds,
                    previous_attempts=previous_attempts,
                )
                st.session_state.ai_report_error = None

            st.rerun()

    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    elif st.session_state.ai_report_error:
        st.error("The AI report could not be generated.")
        st.code(st.session_state.ai_report_error)

        if st.button("Retry AI report"):
            st.session_state.ai_report_error = None
            st.rerun()

    st.divider()

    with st.expander("Review your answers"):
        for number, item in enumerate(answers, start=1):
            mark = "✅" if item["is_correct"] else "❌"
            st.markdown(
                f"**{number}. {mark} {item['category']}**"
            )
            st.write(item["question"])
            st.write(f"Your answer: {item['chosen']}")

            if not item["is_correct"]:
                st.write(f"Correct answer: {item['correct']}")

            st.caption(
                f"Difficulty: {item.get('difficulty', 'Unknown')} · "
                f"Response time: {item['seconds']:.1f} seconds"
            )
            st.divider()

    if st.button("Start a new assessment", use_container_width=True):
        clear_assessment_state()
        st.session_state.pop("assessment_saved_run_id", None)
        st.rerun()


# =========================================================
# 7. FOOTER
# =========================================================

st.markdown("---")
st.caption(
    "MINDTRACE · Cognitive practice, personalized feedback, "
    "continuous improvement."
)

