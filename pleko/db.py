"Pleko database resources."

import copy
import json
import os.path
import sqlite3

import flask

import pleko.master
from pleko import utils
from pleko.user import login_required


def get_dbs(public=True):
    "Get a list of all databases."
    sql = "SELECT dbid, owner, description, public, created, modified FROM dbs"
    if public:
        sql += " WHERE public=1"
    cursor = pleko.master.cursor()
    cursor.execute(sql)
    return [{'dbid':        row[0],
             'owner':       row[1],
             'description': row[2],
             'public':      bool(row[3]),
             'created':     row[4],
             'modified':    row[5]}
            for row in cursor]

def get_db(dbid):
    """Return the database metadata for the given identifier.
    Return None if no such database.
    Does *not* check access.
    """
    cursor = pleko.master.cursor()
    sql = "SELECT owner, description, public, profile," \
          " created, modified FROM dbs WHERE dbid=?"
    cursor.execute(sql, (dbid,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    return {'dbid':        dbid,
            'owner':       row[0],
            'description': row[1],
            'public':      bool(row[2]),
            'profile':     json.loads(row[3]),
            'created':     row[4],
            'modified':    row[5]}

def dbpath(dbid):
    "Return the file path for the given database identifier."
    path = os.path.join(flask.current_app.config['DBS_DIRPATH'], dbid)
    return path + '.sqlite3'
    
def get_cnx(dbid):
    "Get a connection for the given database identifier."
    return sqlite3.connect(dbpath(dbid))

def has_read_access(db):
    "Does the current user (if any) have read access to the database?"
    if db['public']: return True
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_read(dbid):
    """Get the database and check that the current user as read access.
    Raise ValueError if any problem.
    """
    db = get_db(dbid)
    if db is None:
        raise ValueError('no such database')
    if not has_read_access(db):
        raise ValueError('may not read the database')
    return db

def has_write_access(db):
    "Does the current user (if any) have write access to the database?"
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_write(dbid):
    """Get the database and check that the current user as write access.
    Raise ValueError if any problem.
    """
    db = get_db(dbid)
    if db is None:
        raise ValueError('no such db')
    if not has_write_access(db):
        raise ValueError('may not write to the db')
    return db


blueprint = flask.Blueprint('db', __name__)

@blueprint.route('/', methods=["GET", "POST"])
@login_required
def create():
    if utils.is_method_GET():
        return flask.render_template('db/create.html')
    elif utils.is_method_POST():
        try:
            with DbContext() as ctx:
                ctx.set_dbid(flask.request.form['dbid'])
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/<id:dbid>')
def index(dbid):
    try:
        db = get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('db/index.html',
                                 db=db,
                                 has_write_access=has_write_access(db))

@blueprint.route('/<id:dbid>/logs')
def logs(dbid):
    try:
        db = get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cursor = pleko.master.cursor()
    sql = "SELECT new, editor, remote_addr, user_agent, timestamp" \
          " FROM dbs_logs WHERE dbid=? ORDER BY timestamp DESC"
    cursor.execute(sql, (db['dbid'],))
    logs = [{'new': json.loads(row[0]),
             'editor': row[1],
             'remote_addr': row[2],
             'user_agent': row[3],
             'timestamp': row[4]}
            for row in cursor]
    return flask.render_template('db_logs.html',
                                 db=db,
                                 logs=logs)

class DbContext:
    "Context for creating, modifying and saving a database metadata."

    def __init__(self, db=None):
        if db is None:
            self.db = {'owner': flask.g.current_user['username'],
                       'profile': {},
                       'created': utils.get_time()}
            self.orig = {}
        else:
            self.db = db
            self.orig = copy.deepcopy(db)

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['dbid', 'owner']:
            if not self.db.get(key):
                raise ValueError("invalid db: %s not set" % key)
        self.db['modified'] = utils.get_time()
        cursor = pleko.master.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbs WHERE dbid=?",
                       (self.db['dbid'],))
        rows = list(cursor)
        cnx = pleko.master.get()
        with cnx:
            # Update database in master
            if rows[0][0]:
                sql = "UPDATE dbs SET owner=?, description=?," \
                      " public=?, profile=?, modified=?" \
                      " WHERE dbname=?"
                cnx.execute(sql, (self.db['owner'],
                                  self.db.get('description'),
                                  bool(self.db.get('public')),
                                  json.dumps(self.db['profile'],
                                             ensure_ascii=False),
                                  self.db['modified'],
                                  self.db['dbid']))
            # Create database in master, meta info in JSON, and Sqlite file
            else:
                try:
                    db = sqlite3.connect(dbpath(self.db['dbid']))
                except sqlite3.Error as error:
                    raise ValueError(str(error))
                else:
                    db.close()
                sql = "INSERT INTO dbs" \
                      " (dbid, owner, description, public, profile," \
                      "  created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?)"
                cnx.execute(sql, (self.db['dbid'],
                                  self.db['owner'],
                                  self.db.get('description'),
                                  bool(self.db.get('public')),
                                  json.dumps(self.db['profile'],
                                             ensure_ascii=False),
                                  self.db['created'], 
                                  self.db['modified']))
            # Add log entry
            new = {}
            for key, value in self.db.items():
                if value != self.orig.get(key):
                    new[key] = value
            new.pop('modified')
            try:
                editor = flask.g.current_user['username']
            except AttributeError:
                editor = None
            if flask.has_request_context():
                remote_addr = str(flask.request.remote_addr)
                user_agent = str(flask.request.user_agent)
            else:
                remote_addr = None
                user_agent = None
            sql = "INSERT INTO dbs_logs (dbid, new, editor," \
                  " remote_addr, user_agent, timestamp)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
            cnx.execute(sql, (self.db['dbid'],
                              json.dumps(new, ensure_ascii=False),
                              editor,
                              remote_addr,
                              user_agent,
                              utils.get_time()))

    def set_dbid(self, dbid):
        if 'dbid' in self.db:
            raise ValueError('db identifier cannot be changed')
        if not pleko.constants.IDENTIFIER_RX.match(dbid):
            raise ValueError('invalid db identifier')
        if get_db(dbid):
            raise ValueError('db identifier already in use')
        self.db['dbid'] = dbid

    def set_description(self, description):
        self.db['description'] = description or None
