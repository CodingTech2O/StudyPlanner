from datetime import date

# How much each factor counts toward the final split. Must add up to 1.
STRENGTH_WEIGHT = 0.7   # weaker subjects (low Strength) get more time
DATE_WEIGHT = 0.3       # sooner exams get more time


def compute_study_plan(topics, total_time, today=None):
    """Split total_time across topics based on weakness and exam urgency.

    Each topic gets two weights:
    - strength_weight: 6 - Strength, so a Strength of 1 (weak) outweighs a 5 (strong) 5-to-1.
    - urgency_weight: 1 / days_left, so a closer exam outweighs a distant one.

    Both weights are normalized into shares (they sum to 1 across all topics)
    before being blended by STRENGTH_WEIGHT / DATE_WEIGHT, so the result
    always adds up to total_time exactly and never divides by zero.
    """
    if not topics or total_time <= 0:
        return topics

    today = today or date.today()

    strength_weights = [6 - t["Strength"] for t in topics]
    days_left = [
        max((date.fromisoformat(t["Date of Exam"]) - today).days, 1)
        for t in topics
    ]
    urgency_weights = [1 / d for d in days_left]

    strength_total = sum(strength_weights)
    urgency_total = sum(urgency_weights)

    plan = []
    for topic, s_weight, u_weight in zip(topics, strength_weights, urgency_weights):
        share = (
            STRENGTH_WEIGHT * (s_weight / strength_total)
            + DATE_WEIGHT * (u_weight / urgency_total)
        )
        plan.append({**topic, "Allocated Hours": round(total_time * share, 1)})

    return plan
