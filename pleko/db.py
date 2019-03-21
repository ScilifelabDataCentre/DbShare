"Pleko database endpoints."

import copy
import csv
import json
import os
import os.path
import shutil
import sqlite3

import flask

import pleko.master
import pleko.table
from pleko import constants
from pleko import utils
from pleko.user import login_required


def get_dbs(public=True):
    "Get a list of all databases."
    sql = "SELECT id, owner, description, public, created, modified FROM dbs"
    if public:
        sql += " WHERE public=1"
    cursor = pleko.master.cursor()
    cursor.execute(sql)
    return [{'id':          row[0],
             'owner':       row[1],
             'description': row[2],
             'public':      bool(row[3]),
             'created':     row[4],
             'modified':    row[5]}
            for row in cursor]

def get_db(id):
    """Return the database metadata for the given identifier.
    Return None if no such database.
    Does *not* check access.
    """
    cursor = pleko.master.cursor()
    sql = "SELECT owner, description, public, profile," \
          " created, modified FROM dbs WHERE id=?"
    cursor.execute(sql, (id,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    return {'id':          id,
            'owner':       row[0],
            'description': row[1],
            'public':      bool(row[2]),
            'profile':     json.loads(row[3]),
            'created':     row[4],
            'modified':    row[5]}

def get_tables(dbid, schema=False):
    """Get the tables in the database with their number of rows.
    If schema is True, get the table schemas.
    """
    cursor = get_cnx(dbid).cursor()
    sql = "SELECT name FROM sqlite_master WHERE type=?"
    cursor.execute(sql, ('table',))
    tables = [{'id': row[0]} for row in cursor]
    for table in tables:
        table['nrows'] = pleko.table.get_nrows(table['id'], cursor)
    if schema:
        for table in tables:
            table['schema'] = pleko.table.get_schema(table['id'], cursor)
    return tables

def dbpath(dbid):
    "Return the file path for the given database identifier."
    path = os.path.join(flask.current_app.config['DBS_DIRPATH'], dbid)
    return path + '.sqlite3'
    
def get_cnx(dbid):
    "Get a connection for the given database identifier."
    # This will be closed by app.finalize
    flask.g.dbcnx = sqlite3.connect(dbpath(dbid))
    return flask.g.dbcnx

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
        raise ValueError('no such database')
    if not has_write_access(db):
        raise ValueError('may not write to the database')
    return db


blueprint = flask.Blueprint('db', __name__)

@blueprint.route('/', methods=['GET', 'POST'])
@login_required
def create():
    "Create a database."
    if utils.is_method_GET():
        return flask.render_template('db/create.html')

    elif utils.is_method_POST():
        try:
            with DbContext() as ctx:
                ctx.set_id(flask.request.form['id'])
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.index', dbid=ctx.db['id']))

@blueprint.route('/<id:dbid>', methods=['GET', 'POST', 'DELETE'])
def index(dbid):
    "Display database tables and metadata. Delete database."
    if utils.is_method_GET():
        try:
            db = get_check_read(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        return flask.render_template('db/index.html',
                                     db=db,
                                     tables=get_tables(dbid),
                                     has_write_access=has_write_access(db))

    elif utils.is_method_DELETE():
        try:
            db = get_check_write(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        cnx = pleko.master.get_cnx()
        with cnx:
            sql = 'DELETE FROM dbs_logs WHERE id=?'
            cnx.execute(sql, (dbid,))
            sql = 'DELETE FROM dbs WHERE id=?'
            cnx.execute(sql, (dbid,))
            os.remove(dbpath(dbid))
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/<id:dbid>/rename', methods=['GET', 'POST'])
@login_required
def rename(dbid):
    "Rename the database."
    try:
        db = get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))

    if utils.is_method_GET():
        return flask.render_template('db/rename.html', db=db)

    elif utils.is_method_POST():
        try:
            with DbContext(db) as ctx:
                ctx.set_id(flask.request.form['id'])
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.index', dbid=ctx.db['id']))
        

@blueprint.route('/<id:dbid>/logs')
def logs(dbid):
    "Display the logs for a database."
    try:
        db = get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cursor = pleko.master.cursor()
    sql = "SELECT new, editor, remote_addr, user_agent, timestamp" \
          " FROM dbs_logs WHERE id=? ORDER BY timestamp DESC"
    cursor.execute(sql, (db['id'],))
    logs = [{'new':         json.loads(row[0]),
             'editor':      row[1],
             'remote_addr': row[2],
             'user_agent':  row[3],
             'timestamp':   row[4]}
            for row in cursor]
    return flask.render_template('db_logs.html',
                                 db=db,
                                 logs=logs)

@blueprint.route('/<id:dbid>/upload', methods=['GET', 'POST'])
@login_required
def upload(dbid):
    "Create a table from the data in a CSV file."
    try:
        db = get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))

    if utils.is_method_GET():
        return flask.render_template('db/upload.html', db=db)

    elif utils.is_method_POST():
        try:
            cnx = get_cnx(dbid)
            cursor = cnx.cursor()
            csvfile = flask.request.files['csvfile']
            try:
                tableid = flask.request.form['tableid']
                if not tableid: raise KeyError
            except KeyError:
                tableid = os.path.basename(csvfile.filename)
                tableid = os.path.splitext(tableid)[0]
            try:
                pleko.table.get_schema(tableid, cursor)
            except ValueError:
                pass
            else:
                raise ValueError('table identifier already in use')
            schema = {'id': tableid}

            # Preprocess CSV data
            lines = csvfile.read().decode('utf-8').split('\n')
            records = list(csv.reader(lines))
            header = records.pop(0)
            if len(header) == 0:
                raise ValueError('empty header record in the CSV file')
            for id in header:
                if not constants.IDENTIFIER_RX.match(id):
                    raise ValueError('invalid header column identifier')
            if len(header) != len(set(header)):
                raise ValueError('non-unique header column identifier')
            # Eliminate empty records
            records = [r for r in records if r]

            # Infer column types and constraints
            schema['columns'] = [{'id': id} for id in header]
            for i, column in enumerate(schema['columns']):

                # First attempt: integer
                column['notnull'] = True
                type = None
                for n, record in enumerate(records):
                    value = record[i]
                    if value:
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            break
                    else:
                        column['notnull'] = False
                else:
                    type = constants.INTEGER

                # Next attempt: float
                if type is None:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value:
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                break
                        else:
                            column['notnull'] = False
                    else:
                        type = constants.REAL

                # Default: text
                if type is None:
                    column['type'] = constants.TEXT
                    if column['notnull']:
                        for record in records:
                            if not record[i]:
                                column['notnull'] = False
                                break
                else:
                    column['type'] = type

            pleko.table.create_table(schema, cursor)

            # Actually convert values in records
            for i, column in enumerate(schema['columns']):
                type = column['type']
                if type == constants.INTEGER:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value:
                            record[i] = int(value)
                        else:
                            record[i] = None
                elif type == constants.REAL:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value:
                            record[i] = float(value)
                        else:
                            record[i] = None
                else:
                    for n, record in enumerate(records):
                        if not record[i]:
                            record[i] = None
            # Insert the data
            with cnx:
                sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                      (tableid,
                       ','.join([c['id'] for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                cursor.executemany(sql, records)
            flask.flash("Added %s rows" % len(records), 'message')

        except (ValueError, IndexError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.upload',
                                                dbid=dbid,
                                                tableid=tableid))
        return flask.redirect(flask.url_for('table.rows',
                                            dbid=dbid,
                                            tableid=tableid))

@blueprint.route('/<id:dbid>/clone', methods=['GET', 'POST'])
@login_required
def clone(dbid):
    "Create a clone of the database."
    try:
        db = get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))

    if utils.is_method_GET():
        return flask.render_template('db/clone.html', db=db)

    elif utils.is_method_POST():
        try:
            with DbContext() as ctx:
                ctx.set_id(flask.request.form['id'])
                ctx.set_description(flask.request.form.get('description'))
                ctx.db['profile'] = db['profile']
                ctx.db['origin'] = dbid # Will show up in logs
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone', dbid=dbid))
        shutil.copy(dbpath(dbid), dbpath(ctx.db['id']))
        return flask.redirect(flask.url_for('.index', dbid=ctx.db['id']))


class DbContext:
    "Context for creating, modifying and saving a database metadata."

    def __init__(self, db=None):
        if db is None:
            self.db = {'owner':   flask.g.current_user['username'],
                       'public': False,
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
        for key in ['id', 'owner']:
            if not self.db.get(key):
                raise ValueError("invalid db: %s not set" % key)
        self.db['modified'] = utils.get_time()
        cnx = pleko.master.get() # Don't close this; may be needed elsewhere
        cursor = cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbs WHERE id=?",
                       (self.db['id'],))
        row = cursor.fetchone()
        # If new database, then do not overwrite existing
        if not self.orig and row[0] != 0:
            raise ValueError('database identifier already in use')
        with cnx:
            # Create database in master, and Sqlite file
            if row[0] == 0:
                try:
                    db = sqlite3.connect(dbpath(self.db['id']))
                except sqlite3.Error as error:
                    raise ValueError(str(error))
                else:
                    db.close()
                sql = "INSERT INTO dbs" \
                      " (id, owner, description, public, profile," \
                      "  created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?)"
                cnx.execute(sql, (self.db['id'],
                                  self.db['owner'],
                                  self.db.get('description'),
                                  bool(self.db.get('public')),
                                  json.dumps(self.db['profile'],
                                             ensure_ascii=False),
                                  self.db['created'], 
                                  self.db['modified']))
            # Update database in master
            else:
                sql = "UPDATE dbs SET owner=?, description=?," \
                      " public=?, profile=?, modified=?" \
                      " WHERE id=?"
                cnx.execute(sql, (self.db['owner'],
                                  self.db.get('description'),
                                  bool(self.db.get('public')),
                                  json.dumps(self.db['profile'],
                                             ensure_ascii=False),
                                  self.db['modified'],
                                  self.db['id']))
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
            sql = "INSERT INTO dbs_logs (id, new, editor," \
                  " remote_addr, user_agent, timestamp)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
            cnx.execute(sql, (self.db['id'],
                              json.dumps(new, ensure_ascii=False),
                              editor,
                              remote_addr,
                              user_agent,
                              utils.get_time()))

    def set_id(self, id):
        "Set or change the database identifier."
        if not constants.IDENTIFIER_RX.match(id):
            raise ValueError('invalid database identifier')
        if get_db(id):
            raise ValueError('database identifier already in use')
        try:
            oldid =self.db['id']
        except KeyError:
            pass
        else:
            cnx = pleko.master.get()
            with cnx:
                cnx.execute('PRAGMA foreign_keys=OFF')
                sql = "UPDATE dbs SET id=? WHERE id=?"
                cnx.execute(sql, (id, oldid))
                sql = "UPDATE dbs_logs SET id=? WHERE id=?"
                cnx.execute(sql, (id, oldid))
                cnx.execute('PRAGMA foreign_keys=ON')
            os.rename(dbpath(oldid), dbpath(id))
        self.db['id'] = id

    def set_description(self, description):
        "Set the database description."
        self.db['description'] = description or None
