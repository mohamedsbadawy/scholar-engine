# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')  # Fixed the label

class PasswordResetForm(FlaskForm):
    password1 = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Reset Password')

class LoginForm(FlaskForm):
    email_login = StringField('Email', validators=[DataRequired(), Email()])
    password_login = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    first_name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password1')])
    captcha_answer = StringField('Captcha Answer', validators=[DataRequired()])
    submit = SubmitField('Create Account')