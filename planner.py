from datetime import date, timedelta

# How much each factor counts toward the final split. Must add up to 1.
STRENGTH_WEIGHT = 0.7   # weaker subjects (low Strength) get more time
DATE_WEIGHT = 0.3       # sooner exams get more time

# Rules for the day-by-day schedule.
EXAM_EVE_SHARE = 0.10        # of a subject's hours, saved for the day before its exam
FOCUS_DAY_SPLIT = (8, 2)     # subject with the most hours left : subject with the fewest
REVISION_DAY_SPLIT = (3, 7)  # weakest subject's revision : subject with the most hours left


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


def build_daily_schedule(plan, today=None):
    """Spread each subject's allocated hours over the days from today to the last exam eve.

    A subject keeps EXAM_EVE_SHARE of its hours for the day before its exam. The
    rest is studied on the days before that, and those days alternate:
    - focus day (1st, 3rd, ...): the subject with the most hours left and the one
      with the fewest share the day FOCUS_DAY_SPLIT.
    - revision day (2nd, 4th, ...): the weakest subject is revised and the subject
      with the most hours left is studied, REVISION_DAY_SPLIT. If that is the
      same subject, the study slot goes to the one with the next most hours.

    A day's length is the hours still to place divided by the days still to go, so
    the plan finishes on the last exam eve. Time is counted in whole minutes so a
    subject's blocks add up to its allocated hours exactly. Hours a subject could
    not get in before its own exam eve land on that day as a "Catch-up" block.
    """
    if not plan:
        return []

    today = today or date.today()

    subjects = []
    for topic in plan:
        minutes = round(topic["Allocated Hours"] * 60)
        eve_minutes = round(minutes * EXAM_EVE_SHARE)
        exam = date.fromisoformat(topic["Date of Exam"])
        subjects.append({
            "name": topic["Subject"],
            "strength": topic["Strength"],
            # An exam that is today or already past has its eve today, as in compute_study_plan.
            "eve": max(exam - timedelta(days=1), today),
            "eve_minutes": eve_minutes,
            "left": minutes - eve_minutes,
        })

    last_eve = max(s["eve"] for s in subjects)
    schedule = []

    for offset in range((last_eve - today).days + 1):
        day = today + timedelta(days=offset)
        blocks = []

        for s in subjects:
            if s["eve"] == day:
                _add_block(blocks, s, "Exam eve", s["eve_minutes"])
                _add_block(blocks, s, "Catch-up", s["left"])
                s["left"] = 0

        split = None
        active = [s for s in subjects if s["eve"] > day and s["left"] > 0]
        if active:
            focus_day = offset % 2 == 0
            split = FOCUS_DAY_SPLIT if focus_day else REVISION_DAY_SPLIT
            days_left = (last_eve - day).days
            budget = -(-sum(s["left"] for s in active) // days_left)  # ceiling division
            blocks += _spend(active, _day_requests(active, budget, focus_day), budget)

        schedule.append({
            "Date": day,
            "Split": f"{split[0]}:{split[1]}" if split else None,
            "Blocks": blocks,
            "Minutes": sum(b["Minutes"] for b in blocks),
        })

    return schedule


def _by_hours_left(subject):
    """Sort key: most hours left first, the sooner exam winning a tie."""
    return (-subject["left"], subject["eve"])


def _day_requests(active, budget, focus_day):
    """The two (subject, minutes, kind) slots a day's budget is split into."""
    by_hours = sorted(active, key=_by_hours_left)

    if focus_day:
        first, second = by_hours[0], by_hours[-1]
        kinds, split = ("Study", "Study"), FOCUS_DAY_SPLIT
    else:
        first = min(active, key=lambda s: (s["strength"], s["eve"]))
        others = [s for s in by_hours if s is not first]
        second = others[0] if others else first
        kinds, split = ("Revision", "Study"), REVISION_DAY_SPLIT

    first_minutes = round(budget * split[0] / sum(split))
    return [(first, first_minutes, kinds[0]), (second, budget - first_minutes, kinds[1])]


def _spend(active, requests, budget):
    """Turn requests into blocks, never taking more than a subject has left.

    Minutes a subject can't cover because it ran out go to whoever has the most
    left, so the day still adds up to budget.
    """
    blocks = []
    for subject, minutes, kind in requests:
        taken = min(minutes, subject["left"])
        subject["left"] -= taken
        _add_block(blocks, subject, kind, taken)

    shortfall = budget - sum(b["Minutes"] for b in blocks)
    for subject in sorted(active, key=_by_hours_left):
        taken = min(shortfall, subject["left"])
        subject["left"] -= taken
        shortfall -= taken
        _add_block(blocks, subject, "Study", taken)

    return blocks


def _add_block(blocks, subject, kind, minutes):
    """Add minutes of kind for subject, merging into a block it already has."""
    if minutes <= 0:
        return
    for block in blocks:
        if block["Subject"] == subject["name"] and block["Kind"] == kind:
            block["Minutes"] += minutes
            return
    blocks.append({"Subject": subject["name"], "Kind": kind, "Minutes": minutes})
