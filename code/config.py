import os

DEBUG = True
DB_NAME = 'dev.db'
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)
SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH)
