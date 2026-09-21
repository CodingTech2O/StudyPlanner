# 📚 Study Planner

A small Flask app for planning your study time: log how many hours you can commit, add the subjects you're revising, and track your confidence in each one as exam day approaches.

## Features

- **Set your study budget** &mdash; enter the total hours you can give, once, at the start.
- **Add subjects** &mdash; each with a confidence rating (1-5, via a slider) and an exam date.
- **Visual dashboard** &mdash; subjects are shown as cards with an animated, colour-coded confidence bar (red &rarr; amber &rarr; green).
- **Auto-generated study plan** &mdash; once you've set your hours and added subjects, each card shows how many of those hours it should get, weighted by how weak you are in it and how soon its exam is (see `planner.py`).
- **Day-by-day schedule** &mdash; the hours are laid out per day from today until the last exam eve (see [How the schedule works](#how-the-schedule-works)).
- **Delete subjects** &mdash; remove a topic once you've covered it (with a confirmation prompt).
- **Responsive, animated UI** &mdash; light/dark theme (follows your OS setting), smooth transitions, and no build step required.

## Tech stack

- [Flask](https://flask.palletsprojects.com/) + [Flask-WTF](https://flask-wtf.readthedocs.io/) for the server and forms
- Jinja2 templates
- Vanilla CSS and JavaScript (no frontend build tooling)
- JSON file storage (`data/topics.json`)
- [uv](https://docs.astral.sh/uv/) for dependency management

## Getting started

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Set a secret key** (used for form security). Create a `.env` file in the project root:

   ```env
   SECRET_KEY=change-this-to-something-random
   ```

   If you skip this, the app falls back to an insecure development key, so don't rely on that outside local testing.

3. **Run the app**

   ```bash
   uv run app.py
   ```

4. Open [http://localhost:6767](http://localhost:6767) in your browser.

## Usage

1. On first visit, enter how many hours you can give to studying in total.
2. Click **+ Add Topic** to add a subject: give it a name, rate your confidence from 1 (weak) to 5 (strong) with the slider, and pick its exam date.
3. Your dashboard shows each subject as a card with a confidence bar and exam date.
4. Click the **&times;** on a card to remove a subject you've finished with.

## How the schedule works

Each subject's allocated hours (weighted by weakness and exam date) are placed on the calendar like this:

- **Exam eve:** 10% of a subject's hours are kept for the day before its exam.
- **Day 1, 3, 5, ... (focus, 8:2):** the subject with the most hours left gets 80% of the day, the subject with the fewest hours left gets 20%.
- **Day 2, 4, 6, ... (revision, 3:7):** 30% of the day revises your weakest subject, 70% studies the subject with the most hours left (if that's the same subject, the next one down gets the 70%).
- **Day length:** each day is as long as it needs to be for every subject to still finish before its own exam eve. Days can get shorter as the plan goes on, never longer, so nothing is left to cram at the end.
- **Adjusted days:** the splits above don't look at exam dates. When a split would leave a subject with an earlier exam short of time, minutes move to it from the subjects with later exams, only as many as needed, and the day is marked *adjusted*. If an exam is close and needs most of your time, that day can end up almost entirely one subject.
- **Catch-up:** only if an exam is tomorrow (or today) is there no earlier day for a subject's hours; they're then shown as a red *Catch-up* block on its exam eve.

The rules live in constants at the top of `planner.py` (`EXAM_EVE_SHARE`, `FOCUS_DAY_SPLIT`, `REVISION_DAY_SPLIT`).

## Project structure

```text
Study Planner/
├── app.py                 # Flask routes (index, add_topic, delete)
├── forms.py                # WTForms definitions (TopicForm, TotalStudyTime)
├── planner.py               # Study-hour allocation + day-by-day schedule
├── data/
│   └── topics.json         # Stored subjects
├── templates/
│   ├── base.html            # Shared layout (header, nav, static links)
│   ├── index.html           # Dashboard / onboarding view
│   └── add.html              # Add-subject form
└── static/
    ├── CSS/style.css        # Styling, theming, animations
    └── JS/main.js            # Progress-bar animation, slider label, delete confirm
```

## License

MIT &mdash; see [LICENSE](LICENSE).
