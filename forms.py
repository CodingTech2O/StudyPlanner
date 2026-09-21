from wtforms import StringField, IntegerRangeField,DateField,IntegerField, SubmitField
from flask_wtf import FlaskForm

class TopicForm(FlaskForm):
    subject = StringField("Subject: ")
    strength = IntegerRangeField(
        "1-5: ",
        render_kw={"min": 1, "max": 5, "value": 3}
    )
    date_of_exam = DateField("Exam Date")
    submit = SubmitField("Submit ")


class TotalStudyTime(FlaskForm):
    time = IntegerField(
        "Time you can give in hrs",   )
    submit = SubmitField("Submit")