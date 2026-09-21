# 📚 Study Planner

A small Flask app for planning your study time: log how many hours you can commit, add the subjects you're revising, and track your confidence in each one as exam day approaches.

## Features

- **Set your study budget** &mdash; enter the total hours you can give, once, at the start.
- **Add subjects** &mdash; each with a confidence rating (1-5, via a slider) and an exam date.
- **Visual dashboard** &mdash; subjects are shown as cards with an animated, colour-coded confidence bar (red &rarr; amber &rarr; green).
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

## Project structure

```text
Study Planner/
├── app.py                 # Flask routes (index, add_topic, delete)
├── forms.py                # WTForms definitions (TopicForm, TotalStudyTime)
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
