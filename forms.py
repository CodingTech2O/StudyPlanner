from wtforms import StringField, IntegerRangeField,DateField,IntegerField, SubmitField
from flask_wtf import FlaskForm

class TopicForm(FlaskForm):
    subject = StringField("Subject: ")
    strength = IntegerField("1-5: ")
    date_of_exam = DateField("Exam Date")
    submit = SubmitField("Submit ")

class TotalStudyTime(FlaskForm):
    time = IntegerRangeField("Time you can give")
    submit = SubmitField("Submit ")