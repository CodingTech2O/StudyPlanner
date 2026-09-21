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

    Those splits don't know about exam dates, so each day is also checked against
    them: _day_length makes the day long enough for every subject to finish before
    its own exam eve, and _protect_deadlines nudges the split, only as much as
    needed, when it would leave an early exam short. A day marked "Shifted" had
    its split nudged that way.

    Time is counted in whole minutes so a subject's blocks add up to its allocated
    hours exactly. The only hours that can't be placed earlier are those of an exam
    that is today or tomorrow; they land on its eve as a "Catch-up" block.
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
        shifted = False
        active = [s for s in subjects if s["eve"] > day and s["left"] > 0]
        if active:
            focus_day = offset % 2 == 0
            split = FOCUS_DAY_SPLIT if focus_day else REVISION_DAY_SPLIT

            budget = _day_length(active, day)
            shares = _split_day(active, budget, focus_day)
            shifted = _protect_deadlines(active, shares, budget, day)
            for s, kinds in zip(active, shares):
                for kind, minutes in kinds.items():
                    s["left"] -= minutes
                    _add_block(blocks, s, kind, minutes)

        schedule.append({
            "Date": day,
            "Split": f"{split[0]}:{split[1]}" if split else None,
            "Shifted": shifted,
            "Blocks": blocks,
            "Minutes": sum(b["Minutes"] for b in blocks),
        })

    return schedule


def _by_hours_left(subject):
    """Sort key: most hours left first, the sooner exam winning a tie."""
    return (-subject["left"], subject["eve"])


def _day_length(active, day):
    """How many minutes today should be.

    Every exam eve is a deadline: the subjects due by then still need some
    minutes and have some days left (today included), so today has to be at least
    minutes / days. The longest of those is the day. That makes days shorter as
    the plan goes on, never longer, so nothing is left to cram at the end.
    """
    length = 0
    for eve in {s["eve"] for s in active}:
        needed = sum(s["left"] for s in active if s["eve"] <= eve)
        length = max(length, -(-needed // (eve - day).days))  # ceiling division
    return length


def _day_requests(active, budget, focus_day):
    """The two (index into active, minutes, kind) slots a day's budget is split into."""
    everyone = range(len(active))
    by_hours = sorted(everyone, key=lambda i: _by_hours_left(active[i]))

    if focus_day:
        first, second = by_hours[0], by_hours[-1]
        kinds, split = ("Study", "Study"), FOCUS_DAY_SPLIT
    else:
        first = min(everyone, key=lambda i: (active[i]["strength"], active[i]["eve"]))
        others = [i for i in by_hours if i != first]
        second = others[0] if others else first
        kinds, split = ("Revision", "Study"), REVISION_DAY_SPLIT

    first_minutes = round(budget * split[0] / sum(split))
    return [(first, first_minutes, kinds[0]), (second, budget - first_minutes, kinds[1])]


def _split_day(active, budget, focus_day):
    """Share budget out by the day's split.

    Returns {"Study": minutes, "Revision": minutes} for each active subject. A
    subject never gets more than it has left; what it can't take goes to whoever
    has the most left, so budget is used up whenever there's enough to use.
    """
    shares = [{"Study": 0, "Revision": 0} for _ in active]
    spent = 0

    def give(i, kind, minutes):
        nonlocal spent
        taken = min(minutes, active[i]["left"] - sum(shares[i].values()), budget - spent)
        shares[i][kind] += taken
        spent += taken

    for i, minutes, kind in _day_requests(active, budget, focus_day):
        give(i, kind, minutes)
    for i in sorted(range(len(active)), key=lambda i: _by_hours_left(active[i])):
        give(i, "Study", budget - spent)

    return shares


def _protect_deadlines(active, shares, budget, day):
    """Move minutes between subjects so every exam eve can still be reached.

    Take the subjects whose eve is on or before some date. On the days after
    today they can do at most one budget a day, so whatever they need beyond that
    has to be done today. If the split gave them less, the shortfall comes off the
    subjects with the latest exams and goes to the earliest ones.

    The group of everyone needs no check, since the day spends the whole budget.
    Returns whether any minutes were moved.
    """
    def given(i):
        return sum(shares[i].values())

    moved = 0
    for eve in sorted({s["eve"] for s in active})[:-1]:
        group = [i for i, s in enumerate(active) if s["eve"] <= eve]
        others = [i for i, s in enumerate(active) if s["eve"] > eve]

        must_do = sum(active[i]["left"] for i in group) - budget * ((eve - day).days - 1)
        short = must_do - sum(given(i) for i in group)
        if short <= 0:
            continue

        freed = 0
        for i in sorted(others, key=lambda i: active[i]["eve"], reverse=True):
            for kind in ("Study", "Revision"):
                cut = min(short - freed, shares[i][kind])
                shares[i][kind] -= cut
                freed += cut

        for i in sorted(group, key=lambda i: active[i]["eve"]):
            extra = min(freed, active[i]["left"] - given(i))
            shares[i]["Study"] += extra
            freed -= extra
            moved += extra

    return moved > 0


def _add_block(blocks, subject, kind, minutes):
    """Add minutes of kind for subject, merging into a block it already has."""
    if minutes <= 0:
        return
    for block in blocks:
        if block["Subject"] == subject["name"] and block["Kind"] == kind:
            block["Minutes"] += minutes
            return
    blocks.append({"Subject": subject["name"], "Kind": kind, "Minutes": minutes})
