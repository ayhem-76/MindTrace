def wilson_interval(correct, total, z=1.96):
    """Return the Wilson confidence interval as rounded percentages."""
    if total <= 0:
        return 0, 0

    proportion = correct / total
    denominator = 1 + z ** 2 / total
    center = (
        proportion + z ** 2 / (2 * total)
    ) / denominator
    margin = (
        z
        * (
            proportion * (1 - proportion) / total
            + z ** 2 / (4 * total ** 2)
        ) ** 0.5
        / denominator
    )

    lower = max(0, (center - margin) * 100)
    upper = min(100, (center + margin) * 100)
    return round(lower), round(upper)


DIFFICULTY_LEVELS = ["Moderate", "Difficult", "Challenging"]


def next_difficulty(current, is_correct):
    """Move one level up or down while staying within the available levels."""
    current_index = DIFFICULTY_LEVELS.index(current)
    change = 1 if is_correct else -1
    next_index = max(0, min(len(DIFFICULTY_LEVELS) - 1, current_index + change))
    return DIFFICULTY_LEVELS[next_index]


def category_summary(answers, categories):
    """Summarize accuracy, timing, and uncertainty for each category."""
    summary = {}

    for category in categories:
        category_answers = [
            answer for answer in answers if answer["category"] == category
        ]
        correct = sum(answer["is_correct"] for answer in category_answers)
        total = len(category_answers)
        average_seconds = (
            sum(answer["seconds"] for answer in category_answers) / total
            if total else 0
        )
        interval_low, interval_high = wilson_interval(correct, total)

        summary[category] = {
            "correct": correct,
            "total": total,
            "score": round(100 * correct / total) if total else 0,
            "interval_low": interval_low,
            "interval_high": interval_high,
            "average_seconds": round(average_seconds, 2),
        }

    return summary


def processing_speed_score(correct, total, average_seconds):
    """Combine Processing Speed accuracy and response-time performance."""
    if total <= 0:
        return 0

    accuracy_score = 100 * correct / total
    # Rapidness is 100% at <=5s/question and 0% at >=30s/question.
    rapidness_score = max(0, min(100, (30 - average_seconds) / 25 * 100))
    return round(0.7 * accuracy_score + 0.3 * rapidness_score)
