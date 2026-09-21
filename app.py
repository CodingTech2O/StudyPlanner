import json
from flask import Flask, render_template, redirect, url_for
import os
from dotenv import load_dotenv
from forms import TopicForm, TotalStudyTime

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

total_time_to_study = 0

@app.route("/", methods=["GET", "POST"])
def index():
    global total_time_to_study

    with open("data/topics.json", "r") as f:
        data = json.load(f)

    form = None

    if total_time_to_study == 0:
        form = TotalStudyTime()

        if form.validate_on_submit():
            total_time_to_study = form.time.data
            return redirect(url_for("index"))

    return render_template(
        "index.html",
        data=data,
        form=form,
        total_time_to_study=total_time_to_study
    )

@app.route("/add_topic", methods=["GET", "POST"])
def add():
    form = TopicForm()

    if form.validate_on_submit():

        # Load existing topics
        try:
            with open("data/topics.json", "r") as f:
                topics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            topics = []

        # Add new topic
        topic = {
            "Subject": form.subject.data,
            "Strength": form.strength.data,
            "Date of Exam": str(form.date_of_exam.data),
            "Delete URL": url_for(
                "delete",
                subject=form.subject.data
            )
        }

        topics.append(topic)

        # Save topics
        with open("data/topics.json", "w") as f:
            json.dump(topics, f, indent=4)

        return redirect(url_for("index"))

    return render_template("add.html", form=form)


@app.route("/delete/<subject>")
def delete(subject):

    try:
        with open("data/topics.json", "r") as f:
            topics = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        topics = []

    # Remove matching subject
    topics = [
        topic for topic in topics
        if topic["Subject"] != subject
    ]

    with open("data/topics.json", "w") as f:
        json.dump(topics, f, indent=4)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=6767)