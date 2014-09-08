__author__ = 'sikho'

import os
basedir = os.path.abspath(os.path.dirname(__file__))

ADMINS = frozenset(['sikhosonke.manyela@gmail.com'])
SECRET_KEY = 'manyela.'

#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sii.db')

SQLALCHEMY_DATABASE_URI = 'postgresql://jabu:jabu@127.0.0.1:5432/todos'

#SQLALCHEMY_DATABASE_URI = 'mysql://root:manyela@127.0.0.1/vudu'
DATABASE_CONNECT_OPTIONS = {}

FLASKY_COMMENTS_PER_PAGE = 50

DATABASE_QUERY_TIMEOUT = 0.5

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static/upload")
ALLOWED_EXTENSIONS = set(['bmp', 'png', 'jpg', 'jpeg', 'gif'])

THREADS_PER_PAGE = 8

CSRF_ENABLED = True
CSRF_SESSION_KEY = "vala vala"

DEBUG = True


