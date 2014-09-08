__author__ = 'sikho'


from flask_wtf import Form
from wtforms import TextField, PasswordField, validators, HiddenField, TextAreaField, BooleanField, SubmitField, StringField, IntegerField, SelectField, DateField
from wtforms.validators import Required, EqualTo, Optional, Length, Email
from models import *


class SignupForm(Form):
    email = TextField('Email address', validators=[
            Required('Please provide a valid email address'),
            Length(min=6, message=(u'Email address too short')),
            Email(message=(u'That\'s not a valid email address.'))
            ])
    password = PasswordField('Pick a secure password', validators=[
            Required(),
            Length(min=6, message=(u'Please give a longer password'))
            ])
    username = TextField('Choose your username', validators=[Required()])
    agree = BooleanField('I agree all your <a href="/static/tos.html">Terms of Services</a>', validators=[Required(u'You must accept our Terms of Service')])


class SigninForm(Form):
    username = TextField('Username', validators=[
            Required(),
            validators.Length(min=3, message=(u'Your username must be a minimum of 3'))
            ])
    password = PasswordField('Password', validators=[
            Required(),
            validators.Length(min=6, message=(u'Please give a longer password'))
            ])
    remember_me = BooleanField('Remember me', default = False)


class PortoForm(Form):
    portfolio_id = HiddenField()
    title = TextField('Title', validators=[
            validators.Length(min=3, message=(u'Title must be longer, at least 3 characters'))
            ])
    description = TextField('Description', validators=[
            validators.Length(min=10, message=(u'Please give a longer description, at least 10 characters'))
            ])
    tags = TextField('Tags', validators=[
            validators.Length(min=2, message=(u'The tag at least having 2 characters length'))
            ])

class CommentForm(Form):
    body = StringField('', [validators.Required()])
    submit = SubmitField('Submit')


class ContactsForm(Form):
    first_name = TextField("FirstName",  [validators.Required()])
    last_name = TextField("LastName",  [validators.Required()])
    email = TextField("Email",  [validators.Required(), validators.Email()])
    home_number = TextField("WorkNumber")
    work_number = TextField("WorkNumber")
    cell_number = TextField("CellNumber")
    submit = SubmitField("Send")


class AddTask(Form):
    task_id = IntegerField('Priority')
    name = TextField('Task Name', validators=[Required()])
    due_date = DateField('Date Due (yyyy-mm-dd)', validators=[Required()],  format='%Y-%m-%d')
    priority = SelectField('Priority', validators=[Required()],
                            choices=[('1', '1'),('2', '2'),('3', '3'),
                                        ('4', '4'),('5', '5')])
    task_type = SelectField('Type', validators=[Required()],
                            choices=[('1', 'WORK'),('2', 'CUSTOMER'),('3', 'PERSONAL')])
    status = IntegerField('Status')
    state = SelectField('State', validators=[Required()],
                            choices=[('1', 'Todo'),('2', 'Doing'),('3', 'Done')])

    start_date = DateField('Posted Date (yyyy-mm-dd)', validators=[Required()],  format='%Y-%m-%d')