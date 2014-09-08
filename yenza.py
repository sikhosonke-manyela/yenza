from views import *
from models import *
from app import app, db, dbinit, migrate, manager


if __name__ == '__main__':
    dbinit()
    manager.run()
