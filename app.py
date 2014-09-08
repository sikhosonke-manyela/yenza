__author__ = 'sikho'

from flask import Flask
from flask.ext.login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Message, Mail
from flask.ext.security import (
    Security, SQLAlchemyUserDatastore, current_user,
    UserMixin, RoleMixin, login_required
)
from flask.ext.principal import Principal, Permission, RoleNeed
from flask.ext.moment import Moment
from flask.ext.cache import Cache

mail = Mail()
app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

moment = Moment(app)

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin'

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

app.secret_key = 'development key'

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'contact@example.com'
app.config["MAIL_PASSWORD"] = 'your-password'
app.config['SECRET_KEY'] = 'manyela'

mail.init_app(app)


def dbinit():
    #db.drop_all()
    db.create_all()