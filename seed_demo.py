from datetime import datetime, timedelta, timezone

import brain_twin_db as db


DEMO_USERNAME = "demo_user"
DEMO_PASSWORD = "MindTrace-Demo-2026!"

CATEGORIES = [
    "Logic & Patterns",
    "Numerical Reasoning",
    "Spatial Reasoning",
    "Working Memory",
    "Processing Speed",
    "Verbal Reasoning",
]

SCORES_BY_ATTEMPT = [
    [52, 48, 55, 45, 50, 58],
    [58, 54, 60, 52, 56, 61],
    [63, 59, 64, 58, 61, 66],
    [68, 65, 69, 63, 67, 70],
    [73, 70, 74, 69, 72, 75],
    [78, 76, 80, 74, 77, 81],
]


def build_category_scores(scores):
    category_scores = {}

    for category, score in zip(CATEGORIES, scores):
        total = 12
        correct = round(score * total / 100)
        category_scores[category] = {
            "correct": correct,
            "total": total,
            "score": round(100 * correct / total),
            "interval_low": max(0, score - 22),
            "interval_high": min(100, score + 18),
            "average_seconds": round(18 - score / 12, 2),
        }

    return category_scores


def main():
    try:
        user_id = db.create_user(DEMO_USERNAME, DEMO_PASSWORD)
        print(f"Created demo account: {DEMO_USERNAME}")
    except Exception:
        user_id = db.authenticate_user(DEMO_USERNAME, DEMO_PASSWORD)
        if user_id is None:
            raise RuntimeError(
                f"The username {DEMO_USERNAME!r} already exists with a "
                "different password."
            )
        print(f"Reusing demo account: {DEMO_USERNAME}")

    history = db.get_user_history(user_id)
    missing_attempts = max(0, len(SCORES_BY_ATTEMPT) - len(history))
    now = datetime.now(timezone.utc)

    for offset in range(missing_attempts):
        attempt_number = len(history) + offset
        scores = SCORES_BY_ATTEMPT[attempt_number]
        category_scores = build_category_scores(scores)
        correct_count = sum(
            details["correct"] for details in category_scores.values()
        )
        total_questions = sum(
            details["total"] for details in category_scores.values()
        )
        average_seconds = sum(
            details["average_seconds"]
            for details in category_scores.values()
        ) / len(category_scores)

        db.save_assessment(
            user_id=user_id,
            cognitive_index=round(100 * correct_count / total_questions),
            correct_count=correct_count,
            total_questions=total_questions,
            average_seconds=round(average_seconds, 2),
            category_scores=category_scores,
            completed_at=(now - timedelta(days=5 - attempt_number)).isoformat(),
        )

    print(f"Demo credentials: {DEMO_USERNAME} / {DEMO_PASSWORD}")
    print(f"Demo assessments available: {len(db.get_user_history(user_id))}")


if __name__ == "__main__":
    main()