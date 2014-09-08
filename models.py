__author__ = 'sikho'
from collections import OrderedDict
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
import bleach
from markdown import markdown


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column('project_id', db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    active = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship('Task', backref='posted', lazy='dynamic')
    status = db.Column(db.Enum('PLANNED', 'RUNNING', 'FINISHED', name='employee_types'),
                       default='PLANNED')
    messages = db.relationship('Message', backref='pro_message', lazy='dynamic')
    milestones = db.relationship('Milestone', backref='milestones', lazy='dynamic')
    time_sheet = db.relationship('TimeSheet', backref='time_sheets', lazy='dynamic')

    def __init__(self, name, desc):
        self.name = name
        self.desc = desc
        self.start_date = datetime.utcnow()

    def age(self):
        return datetime.now() - self.created_on

    def __repr__(self):
        return '<Project %r>' % self.name


class User(db.Model, object):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column('username', db.String(60), unique=True, index=True)
    password = db.Column('password', db.String(128))
    email = db.Column('email', db.String(60), unique=True, index=True)
    fullname = db.Column(db.String(101))
    currently_live_in = db.Column(db.String(300))
    time_registered = db.Column(db.DateTime)
    tagline = db.Column(db.String(255))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    registered_on = db.Column('registered_on', db.DateTime)
    projects = db.relationship('Project', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='poster', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    calendar = db.relationship('Calendar', backref='calendar', lazy='dynamic')
    event = db.relationship('Event', backref='event', lazy='dynamic')
    file_attachment = db.relationship('FileAttachment', backref='project_file', lazy='dynamic')
    contact = db.relationship('Contact', backref='contact', lazy='dynamic')
    portfolio = db.relationship('Portfolio')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.username

    def _asdict(self):
        result = OrderedDict()
        for key in self.__mapper__.c.keys():
            result[key] = getattr(self, key)
        return result


groups = db.Table('groups', db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                  db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)

group_to_group = db.Table('group_to_group', db.Column('parent_id', db.Integer, db.ForeignKey('group.id'),
                                                      primary_key=True),
                          db.Column('child_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), unique=True)
    description = db.Column(db.Text)
    tags = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def _asdict(self):
        result = OrderedDict()
        for key in self.__mapper__.c.keys():
            result[key] = getattr(self, key)
        return result


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    users = db.relationship('User',
                            secondary=groups,
                            backref=db.backref('groups',
                                               lazy='dynamic',
                                               order_by=name
                            )
    )
    parents = db.relationship('Group',
                              secondary=group_to_group,
                              primaryjoin=id == group_to_group.c.parent_id,
                              secondaryjoin=id == group_to_group.c.child_id,
                              backref="children",
                              remote_side=[group_to_group.c.parent_id])

    def __repr__(self):
        return self.name

# Define models
roles_users = db.Table('roles_users',db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __init__(self,name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.name


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    due_date = db.Column(db.Date, index=True)
    start_date = db.Column(db.Date, index=True)
    end_date = db.Column(db.Date)
    done = db.Column(db.Boolean)
    priority = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='task', lazy='dynamic')
    messages = db.relationship('Message', backref='imessage', lazy='dynamic')
    file_attach = db.relationship('FileAttachment', backref='task_file', lazy='dynamic')
    time_sheet = db.relationship('TimeSheet', backref='time_sheet', lazy='dynamic')
    deleted = db.Column(db.Boolean)
    task_type = db.Column(db.Integer) # PERSONAL", "CUSTOMER", "WORK"#

    # Todo, Doing, Done
    state = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))

    def __init__(self, name, due_date, status, start_date, task_type, state, deleted=None, desc=None):
        self.name = name
        self.desc = desc
        self.due_date = due_date
        self.start_date = start_date
        self.status = status
        self.deleted = deleted
        self.task_type = task_type
        self.state = state
        self.done = False

    def __repr__(self):
        return '<name %r>' % self.name

    def age(self):
        return datetime.now() - self.created_on


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    approved = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))

    def __init__(self, body):
        self.body=body

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i','strong']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),tags=allowed_tags, strip=True))
db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    subject = db.Column(db.String)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    create_time = db.Column(db.DateTime, index=True,default=datetime.utcnow)
    modified_time = db.Column(db.DateTime)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    deleted = db.Column(db.Boolean)


class FileAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    path = db.Column(db.String(1000))
    url = db.Column(db.String(1000))
    is_public = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, path, url, is_public, created_at):
        self.name = name
        self.path = path
        self.url = url
        self.is_public = is_public
        self.created_at = created_at


class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime)
    priority = db.Column(db.Integer)

    def __init__(self, name, description, deadline, created_on, priority):
        self.name = name
        self.description = description
        self.deadline = deadline
        self.created_on = created_on
        self.priority = priority

    def __repr__(self):
        return self.name


    def days_remaining(self):
        diff = self.deadline - datetime.now()

        return diff.days + 1


class TimeSheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, index=True,default=datetime.now)
    end_time = db.Column(db.DateTime,index=True)
    task_id= db.Column(db.Integer, db.ForeignKey('task.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    approved = db.Column(db.Boolean)

    def __init__(self, start_time, end_time, approved):
        self.start_time = start_time
        self.end_time = end_time
        self.approved = False

    def __repr__(self):
        return self.start_time


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    home_number = db.Column(db.String(15))
    work_number = db.Column(db.String(15))
    cell_number = db.Column(db.String(15))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, first_name,last_name, email, home_number, work_number, cell_number):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.home_number = home_number
        self.work_number = work_number
        self.cell_number = cell_number


class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, desc, created_on, end_date):
        self.name = name
        self.desc = desc
        self.created_on = created_on
        self.end_date = end_date

    def __repr__(self):
        return self.name


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    start_date = db.Column(db.DateTime, index=True)
    end_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, desc, start_date, end_date):
        self.name = name
        self.desc = desc
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return self.name