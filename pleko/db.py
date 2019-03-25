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
    sql = "SELECT id, owner, description, public, tables, indexes, views," \
          " access, created, modified FROM dbs"
    if public:
        sql += " WHERE public=1"
    cursor = pleko.master.get_cursor()
    cursor.execute(sql)
    return [{'id':          row[0],
             'owner':       row[1],
             'description': row[2],
             'public':      bool(row[3]),
             'tables':      json.loads(row[4]),
             'indexes':     json.loads(row[5]),
             'views':       json.loads(row[6]),
             'access':      json.loads(row[7]),
             'created':     row[8],
             'modified':    row[9]}
            for row in cursor]

def get_db(id):
    """Return the database metadata for the given identifier.
    Return None if no such database.
    Does *not* check access.
    """
    cursor = pleko.master.get_cursor()
    sql = "SELECT owner, description, public, tables, indexes, views," \
          " access, created, modified FROM dbs WHERE id=?"
    cursor.execute(sql, (id,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    return {'id':          id,
            'owner':       row[0],
            'description': row[1],
            'public':      bool(row[2]),
            'tables':      json.loads(row[3]),
            'indexes':     json.loads(row[4]),
            'views':       json.loads(row[5]),
            'access':      json.loads(row[6]),
            'created':     row[7],
            'modified':    row[8]}

def create_table(cnx, schema):
    "Create the table given by its schema in the connected database."
    # Collect columns forming primary key
    primarykey = []
    for column in schema['columns']:
        if column.get('primarykey'):
            primarykey.append(column['id'])
    # Column definitions, including column constraints
    clauses = []
    for column in schema['columns']:
        coldef = [column['id'], column['type']]
        if column['id'] in primarykey:
            column['notnull'] = True
            if len(primarykey) == 1:
                coldef.append('PRIMARY KEY')
        if column.get('notnull'):
            coldef.append('NOT NULL')
        clauses.append(' '.join(coldef))
    # Primary key
    if len(primarykey) >= 2:
        clauses.append("PRIMARY KEY (%s)" % ','.join(primarykey))
    # Foreign keys
    for foreignkey in schema.get('foreignkeys', []):
        clauses.append("FOREIGN KEY (%s) REFERENCES %s (%s)" %
                       (','.join(foreignkey['columns']),
                        foreignkey['ref'],
                        ','.join(foreignkey['refcolumns'])))
    sql = "CREATE TABLE IF NOT EXISTS %s (%s)" % (schema['id'],
                                                  ', '.join(clauses))
    cnx.execute(sql)

def create_index(cnx, schema):
    "Create an index given by its schema in the connected database."
    sql = ['CREATE']
    if schema.get('unique'):
        sql.append('UNIQUE')
    sql.append('INDEX IF NOT EXISTS')
    sql.append("%s ON %s" % (schema['id'], schema['table']))
    sql.append("(%s)" % ','.join(schema['columns']))
    sql = ' '.join(sql)
    cnx.execute(sql)

def set_tables_nrows(db):
    "Set the number of rows in the tables in the database."
    dbcnx = get_cnx(db['id']).cursor()
    for table in db['tables'].values():
        table['nrows'] = pleko.table.get_nrows(table['id'], dbcnx)

def get_cnx(dbid):
    "Get a connection for the given database identifier."
    try:
        return flask.g.dbcnx[dbid]
    except KeyError:
        # This will be closed by app.finalize
        dbcnx = flask.g.dbcnx[dbid] = sqlite3.connect(utils.dbpath(dbid))
        dbcnx.execute('PRAGMA foreign_keys=ON')
        return dbcnx

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
    "Display the database tables and metadata. Delete the database."
    if utils.is_method_GET():
        try:
            db = get_check_read(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        dbcnx = pleko.db.get_cnx(db['id'])
        for table in db['tables'].values():
            table['nrows'] = pleko.table.get_nrows(table['id'], dbcnx)
        keyfunc = lambda v: v['id']
        return flask.render_template('db/index.html',
                                     db=db,
                                     tables=sorted(db['tables'].values(),
                                                   key=keyfunc),
                                     indexes=sorted(db['indexes'].values(),
                                                    key=keyfunc),
                                     views=sorted(db['views'].values(),
                                                  key=keyfunc),
                                     has_write_access=has_write_access(db))

    elif utils.is_method_DELETE():
        try:
            db = get_check_write(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        with cnx:
            sql = 'DELETE FROM dbs_logs WHERE id=?'
            cnx.execute(sql, (dbid,))
            sql = 'DELETE FROM dbs WHERE id=?'
            cnx.execute(sql, (dbid,))
            os.remove(utils.dbpath(dbid))
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
    cursor = pleko.master.get_cursor()
    sql = "SELECT new, editor, remote_addr, user_agent, timestamp" \
          " FROM dbs_logs WHERE id=? ORDER BY timestamp DESC"
    cursor.execute(sql, (db['id'],))
    logs = [{'new':         json.loads(row[0]),
             'editor':      row[1],
             'remote_addr': row[2],
             'user_agent':  row[3],
             'timestamp':   row[4]}
            for row in cursor]
    return flask.render_template('db/logs.html',
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
            csvfile = flask.request.files['csvfile']
            try:
                tableid = flask.request.form['tableid']
                if not tableid: raise KeyError
            except KeyError:
                tableid = os.path.basename(csvfile.filename)
                tableid = os.path.splitext(tableid)[0]
            if tableid in db['tables']:
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

            with DbContext(db) as ctx:
                ctx.add_table(schema)

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
            cnx = get_cnx(schema['id'])
            cursor = cnx.cursor()
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
                ctx.db['tables']  = db['tables']
                ctx.db['indexes'] = db['indexes']
                ctx.db['access']  = db['access']
                ctx.db['origin']  = dbid # Will show up in logs
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone', dbid=dbid))
        shutil.copy(utils.dbpath(dbid), utils.dbpath(ctx.db['id']))
        return flask.redirect(flask.url_for('.index', dbid=ctx.db['id']))


class DbContext:
    "Context for creating, modifying and saving metadata for a database."

    def __init__(self, db=None):
        if db is None:
            self.db = {'owner':   flask.g.current_user['username'],
                       'public':  False,
                       'tables':  {}, # Key: tableid
                       'indexes': {}, # Key: indexid
                       'views':   {}, # Key: viewid
                       'access':  {},
                       'created': utils.get_time()}
            self.orig = {}
        else:
            self.db = db
            self.orig = copy.deepcopy(db)
            self.dbcnx = get_cnx(db['id'])
        # Don't close this at exit; will be done externally to context
        self.cnx = pleko.master.get_cnx()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['id', 'owner']:
            if not self.db.get(key):
                raise ValueError("invalid db: %s not set" % key)
        self.db['modified'] = utils.get_time()
        cursor = self.cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbs WHERE id=?", (self.db['id'],))
        row = cursor.fetchone()
        # If new database, then do not overwrite existing
        if not self.orig and row[0] != 0:
            raise ValueError('database identifier already in use')
        with self.cnx:
            # Create database in master, and Sqlite file
            if row[0] == 0:
                try:
                    db = sqlite3.connect(utils.dbpath(self.db['id']))
                except sqlite3.Error as error:
                    raise ValueError(str(error))
                else:
                    db.close()
                sql = "INSERT INTO dbs" \
                      " (id, owner, description, public, tables, indexes," \
                      "  views, access, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.db['id'],
                                       self.db['owner'],
                                       self.db.get('description'),
                                       bool(self.db.get('public')),
                                       json.dumps(self.db['tables']),
                                       json.dumps(self.db['indexes']),
                                       json.dumps(self.db['views']),
                                       json.dumps(self.db['access']),
                                       self.db['created'], 
                                       self.db['modified']))
            # Update database in master
            else:
                sql = "UPDATE dbs SET owner=?, description=?, public=?, " \
                      " tables=?, indexes=?, views=?, access=?, modified=?" \
                      " WHERE id=?"
                self.cnx.execute(sql, (self.db['owner'],
                                       self.db.get('description'),
                                       bool(self.db.get('public')),
                                       json.dumps(self.db['tables']),
                                       json.dumps(self.db['indexes']),
                                       json.dumps(self.db['views']),
                                       json.dumps(self.db['access']),
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
            self.cnx.execute(sql, (self.db['id'],
                                   json.dumps(new),
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
            oldid = self.db['id']
        except KeyError:
            pass
        else:
            with self.cnx:
                self.cnx.execute('PRAGMA foreign_keys=OFF')
                sql = "UPDATE dbs SET id=? WHERE id=?"
                self.cnx.execute(sql, (id, oldid))
                sql = "UPDATE dbs_logs SET id=? WHERE id=?"
                self.cnx.execute(sql, (id, oldid))
                self.cnx.execute('PRAGMA foreign_keys=ON')
            os.rename(utils.dbpath(oldid), utils.dbpath(id))
        self.db['id'] = id

    def set_description(self, description):
        "Set the database description."
        self.db['description'] = description or None

    def add_table(self, schema):
        "Create the table in the database and add to the database definition."
        if schema['id'] in self.db['tables']:
            raise ValueError('table identifier already in use')
        create_table(self.dbcnx, schema)
        self.db['tables'][schema['id']] = schema

    def delete_table(self, tableid):
        "Delete the table from the database and from the database definition."
        try:
            self.db['tables'].pop(tableid)
        except KeyError:
            raise ValueError('no such table in database')
        for index in list(self.db['indexes'].values()):
            if index['table'] == tableid:
                self.db['indexes'].pop(index['id'])
                self.dbcnx.execute("DROP INDEX %s" % index['id'])
        self.dbcnx.execute("DROP TABLE %s" % tableid)

    def add_index(self, schema):
        "Create an index in the database and add to the database definition."
        if schema['table'] not in self.db['tables']:
            raise ValueError("no such table %s for index %s" % (schema['table'],
                                                                schema['id']))
        if schema['id'] in self.db['indexes']:
            raise ValueError("index %s already defined" % schema['id'])
        create_index(self.dbcnx, schema)
        self.db['indexes'][schema['id']] = schema

    def delete_index(self, indexid):
        "Delete an index in the database."
        try:
            self.db['indexes'].pop(indexid)
        except KeyError:
            raise ValueError('no such index in database')
        self.dbcnx.execute("DROP INDEX %s" % indexid)

    def create_view(self, schema):
        "Create a view in the database."
        raise NotImplementedError

    def delete_view(self, viewid):
        "Delete a view in the database."
        raise NotImplementedError
