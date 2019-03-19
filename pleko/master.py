"Pleko master database."

import sqlite3

import flask


def get(app=None):
    "Return the existing connection to the master database, else a new one."
    try:
        return flask.g.cnx
    except AttributeError:
        return get_cnx(app=app)

def get_cnx(app=None):
    "Return a new connection to the master database."
    if app is None:
        app = flask.current_app
    cnx = sqlite3.connect(app.config['MASTERDB_FILEPATH'])
    cnx.execute('PRAGMA foreign_keys=ON')
    return cnx

def cursor(app=None):
    "Return a cursor for the master database."
    return get(app=app).cursor()

def init(app):
    "Initialize tables in the master database, if not done."
    cnx = get_cnx(app=app)
    cnx.execute("CREATE TABLE IF NOT EXISTS users"
               "(username TEXT PRIMARY KEY,"
               " email TEXT NOT NULL UNIQUE,"
               " password TEXT,"
               " apikey TEXT,"
               " role TEXT NOT NULL,"
               " status TEXT NOT NULL,"
               " created TEXT NOT NULL,"
               " modified TEXT NOT NULL)")
    cnx.execute("CREATE INDEX IF NOT EXISTS users_apikey_ix"
               " ON users (apikey)")
    cnx.execute("CREATE TABLE IF NOT EXISTS users_logs"
               "(username TEXT NOT NULL REFERENCES users (username),"
               " new TEXT NOT NULL,"
               " editor TEXT,"
               " remote_addr TEXT,"
               " user_agent TEXT,"
               " timestamp TEXT NOT NULL)")
    cnx.execute("CREATE INDEX IF NOT EXISTS users_logs_username_ix"
               " ON users_logs (username)")
    cnx.execute("CREATE TABLE IF NOT EXISTS dbs"
               "(id TEXT PRIMARY KEY,"
               " owner TEXT NOT NULL REFERENCES users (username),"
               " description TEXT,"
               " public INTEGER NOT NULL,"
               " profile TEXT NOT NULL,"
               " created TEXT NOT NULL,"
               " modified TEXT NOT NULL)")
    cnx.execute("CREATE TABLE IF NOT EXISTS dbs_logs"
               "(id TEXT NOT NULL REFERENCES dbs (id),"
               " new TEXT NOT NULL,"
               " editor TEXT,"
               " remote_addr TEXT,"
               " user_agent TEXT,"
               " timestamp TEXT NOT NULL)")
    cnx.execute("CREATE INDEX IF NOT EXISTS dbs_logs_id_ix"
               " ON dbs_logs (id)")
    cnx.close()
