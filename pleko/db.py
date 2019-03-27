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
import pleko.query
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('db', __name__)

@blueprint.route('/', methods=['GET', 'POST'])
@pleko.user.login_required
def create():
    "Create a database."
    if utils.is_method_GET():
        return flask.render_template('db/create.html')

    elif utils.is_method_POST():
        try:
            with DbContext() as ctx:
                ctx.set_name(flask.request.form['name'])
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=ctx.db['name']))

@blueprint.route('/<name:dbname>', methods=['GET', 'POST', 'DELETE'])
def home(dbname):
    "Display the database tables, views and metadata. Delete the database."
    if utils.is_method_GET():
        try:
            db = get_check_read(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        dbcnx = pleko.db.get_cnx(db['name'])
        for table in db['tables'].values():
            table['nrows'] = get_nrows(table['name'], dbcnx)
        for view in db['views'].values():
            view['nrows'] = get_nrows(view['name'], dbcnx)
        return flask.render_template('db/home.html', 
                                     db=db,
                                     has_write_access=has_write_access(db))

    elif utils.is_method_DELETE():
        try:
            db = get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        cnx = pleko.master.get_cnx()
        with cnx:
            sql = 'DELETE FROM dbs_logs WHERE name=?'
            cnx.execute(sql, (dbname,))
            sql = 'DELETE FROM dbs WHERE name=?'
            cnx.execute(sql, (dbname,))
            os.remove(utils.dbpath(dbname))
        return flask.redirect(flask.url_for('home'))

@blueprint.route('/<name:dbname>/rename', methods=['GET', 'POST'])
@pleko.user.login_required
def rename(dbname):
    "Rename the database."
    try:
        db = get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('db/rename.html', db=db)

    elif utils.is_method_POST():
        try:
            with DbContext(db) as ctx:
                ctx.set_name(flask.request.form['name'])
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=ctx.db['name']))

@blueprint.route('/<name:dbname>/logs')
def logs(dbname):
    "Display the logs for a database."
    try:
        db = get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    cursor = pleko.master.get_cursor()
    sql = "SELECT new, editor, remote_addr, user_agent, timestamp" \
          " FROM dbs_logs WHERE name=? ORDER BY timestamp DESC"
    cursor.execute(sql, (db['name'],))
    logs = [{'new':         json.loads(row[0]),
             'editor':      row[1],
             'remote_addr': row[2],
             'user_agent':  row[3],
             'timestamp':   row[4]}
            for row in cursor]
    return flask.render_template('db/logs.html',
                                 db=db,
                                 logs=logs)

@blueprint.route('/<name:dbname>/upload', methods=['GET', 'POST'])
@pleko.user.login_required
def upload(dbname):
    "Create a table from the data in a CSV file."
    try:
        db = get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.is_method_GET():
        return flask.render_template('db/upload.html', db=db)

    elif utils.is_method_POST():
        try:
            csvfile = flask.request.files['csvfile']
            try:
                tablename = flask.request.form['tablename']
                if not tablename: raise KeyError
            except KeyError:
                tablename = os.path.basename(csvfile.filename)
                tablename = os.path.splitext(tablename)[0]
            if tablename in db['tables']:
                raise ValueError('table name already in use')
            schema = {'name': tablename}

            # Preprocess CSV data
            lines = csvfile.read().decode('utf-8').split('\n')
            records = list(csv.reader(lines))
            header = records.pop(0)
            if len(header) == 0:
                raise ValueError('empty header record in the CSV file')
            for name in header:
                if not constants.NAME_RX.match(name):
                    raise ValueError('invalid header column name')
            if len(header) != len(set(header)):
                raise ValueError('non-unique header column name')
            # Eliminate empty records
            records = [r for r in records if r]

            # Infer column types and constraints
            schema['columns'] = [{'name': name} for name in header]
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
            cnx = get_cnx(db['name'])
            cursor = cnx.cursor()
            with cnx:
                sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                      (tablename,
                       ','.join([c['name'] for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                cursor.executemany(sql, records)
            flask.flash("Added %s rows" % len(records), 'message')

        except (ValueError, IndexError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.upload',
                                                dbname=dbname,
                                                tablename=tablename))
        return flask.redirect(flask.url_for('table.rows',
                                            dbname=dbname,
                                            tablename=tablename))

@blueprint.route('/<name:dbname>/clone', methods=['GET', 'POST'])
@pleko.user.login_required
def clone(dbname):
    "Create a clone of the database."
    try:
        db = get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.is_method_GET():
        return flask.render_template('db/clone.html', db=db)

    elif utils.is_method_POST():
        try:
            with DbContext() as ctx:
                ctx.set_name(flask.request.form['name'])
                ctx.set_description(flask.request.form.get('description'))
                ctx.db['tables']  = db['tables']
                ctx.db['indexes'] = db['indexes']
                ctx.db['views']   = db['views']
                ctx.db['access']  = db['access']
                ctx.db['origin']  = dbname # Will show up in logs
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone', dbname=dbname))
        shutil.copy(utils.dbpath(dbname), utils.dbpath(ctx.db['name']))
        return flask.redirect(flask.url_for('.home', dbname=ctx.db['name']))

@blueprint.route('/<name:dbname>/public', methods=['POST'])
@pleko.user.login_required
def public(dbname):
    "Set the database to public access."
    try:
        db = get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        with DbContext(db) as ctx:
            ctx.db['public'] = True
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Database set to public access.', 'message')
    return flask.redirect(flask.url_for('.home', dbname=db['name']))

@blueprint.route('/<name:dbname>/private', methods=['POST'])
@pleko.user.login_required
def private(dbname):
    "Set the database to private access."
    try:
        db = get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        with DbContext(db) as ctx:
            ctx.db['public'] = False
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Database public access revoked.', 'message')
    return flask.redirect(flask.url_for('.home', dbname=db['name']))


@blueprint.route('/<name:dbname>/download')
def download(dbname):
    "Download the Sqlite3 database file."
    try:
        db = get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    return flask.send_file(utils.dbpath(dbname),
                           mimetype='application/x-sqlite3',
                           as_attachment=True)


class DbContext:
    "Context for creating, modifying and saving metadata for a database."

    def __init__(self, db=None):
        if db is None:
            self.db = {'owner':   flask.g.current_user['username'],
                       'public':  False,
                       'tables':  {}, # Key: tablename
                       'indexes': {}, # Key: indexname
                       'views':   {}, # Key: viewname
                       'access':  {},
                       'created': utils.get_time()}
            self.orig = {}
        else:
            self.db = db
            self.orig = copy.deepcopy(db)
            self.dbcnx = get_cnx(db['name'])
        # Don't close this at exit; will be done externally to context
        self.cnx = pleko.master.get_cnx()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['name', 'owner']:
            if not self.db.get(key):
                raise ValueError("invalid db: %s not set" % key)
        self.db['modified'] = utils.get_time()
        cursor = self.cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbs WHERE name=?", (self.db['name'],))
        row = cursor.fetchone()
        # If new database, then do not overwrite existing
        if not self.orig and row[0] != 0:
            raise ValueError('database name already in use')
        with self.cnx:
            # Create database in master, and Sqlite file
            if row[0] == 0:
                try:
                    db = sqlite3.connect(utils.dbpath(self.db['name']))
                except sqlite3.Error as error:
                    raise ValueError(str(error))
                else:
                    db.close()
                sql = "INSERT INTO dbs" \
                      " (name, owner, description, public, tables, indexes," \
                      "  views, access, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.db['name'],
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
                      " WHERE name=?"
                self.cnx.execute(sql, (self.db['owner'],
                                       self.db.get('description'),
                                       bool(self.db.get('public')),
                                       json.dumps(self.db['tables']),
                                       json.dumps(self.db['indexes']),
                                       json.dumps(self.db['views']),
                                       json.dumps(self.db['access']),
                                       self.db['modified'],
                                       self.db['name']))
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
            sql = "INSERT INTO dbs_logs (name, new, editor," \
                  " remote_addr, user_agent, timestamp)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
            self.cnx.execute(sql, (self.db['name'],
                                   json.dumps(new),
                                   editor,
                                   remote_addr,
                                   user_agent,
                                   utils.get_time()))

    def set_name(self, name):
        "Set or change the database name."
        if not constants.NAME_RX.match(name):
            raise ValueError('invalid database name')
        if get_db(name):
            raise ValueError('database name already in use')
        try:
            oldname = self.db['name']
        except KeyError:
            pass
        else:
            with self.cnx:
                self.cnx.execute('PRAGMA foreign_keys=OFF')
                sql = "UPDATE dbs SET name=? WHERE name=?"
                self.cnx.execute(sql, (name, oldname))
                sql = "UPDATE dbs_logs SET name=? WHERE name=?"
                self.cnx.execute(sql, (name, oldname))
                self.cnx.execute('PRAGMA foreign_keys=ON')
            os.rename(utils.dbpath(oldname), utils.dbpath(name))
        self.db['name'] = name

    def set_description(self, description):
        "Set the database description."
        self.db['description'] = description or None

    def add_table(self, schema):
        "Create the table in the database and add to the database definition."
        if schema['name'] in self.db['tables']:
            raise ValueError('name already in use for table')
        if schema['name'] in self.db['views']:
            raise ValueError('name already in use for view')
        create_table(self.dbcnx, schema)
        self.db['tables'][schema['name']] = schema

    def delete_table(self, tablename):
        "Delete the table from the database and from the database definition."
        try:
            self.db['tables'].pop(tablename)
        except KeyError:
            raise ValueError('no such table in database')
        for index in list(self.db['indexes'].values()):
            if index['table'] == tablename:
                self.db['indexes'].pop(index['name'])
                self.dbcnx.execute("DROP INDEX %s" % index['name'])
        self.dbcnx.execute("DROP TABLE %s" % tablename)

    def add_index(self, schema):
        "Create an index in the database and add to the database definition."
        if schema['table'] not in self.db['tables']:
            raise ValueError("no such table %s for index %s" % (schema['table'],
                                                                schema['name']))
        if schema['name'] in self.db['indexes']:
            raise ValueError("index %s already defined" % schema['name'])
        create_index(self.dbcnx, schema)
        self.db['indexes'][schema['name']] = schema

    def delete_index(self, indexname):
        "Delete an index in the database."
        try:
            self.db['indexes'].pop(indexname)
        except KeyError:
            raise ValueError('no such index in database')
        self.dbcnx.execute("DROP INDEX %s" % indexname)

    def add_view(self, schema):
        "Create a view in the database and add to the database definition."
        if not schema.get('name'):
            raise ValueError('no view name defined')
        if not constants.NAME_RX.match(schema['name']):
            raise ValueError('invalid view name')
        if schema['name'] in self.db['tables']:
            raise ValueError('name already in use for table')
        if schema['name'] in self.db['views']:
            raise ValueError('name already in use for view')
        if not schema.get('query'):
            raise ValueError('no query statement defined')
        query = pleko.query.get_sql_query(schema['query'])
        sql = "CREATE VIEW %s AS %s" % (schema['name'], query)
        self.dbcnx.execute(sql)
        self.db['views'][schema['name']] = schema

    def delete_view(self, viewname):
        "Delete a view in the database."
        try:
            self.db['views'].pop(viewname)
        except KeyError:
            raise ValueError('no such view in database')
        self.dbcnx.execute("DROP VIEW %s" % viewname)


# Utility functions

def get_dbs(public=True):
    "Get a list of all databases."
    sql = "SELECT name, owner, description, public, tables, indexes, views," \
          " access, created, modified FROM dbs"
    if public:
        sql += " WHERE public=1"
    cursor = pleko.master.get_cursor()
    cursor.execute(sql)
    result = [{'name':        row[0],
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
    for db in result:
        db['size'] = os.path.getsize(utils.dbpath(db['name']))
    return result

def get_db(name):
    """Return the database metadata for the given name.
    Return None if no such database.
    Does *not* check access.
    """
    cursor = pleko.master.get_cursor()
    sql = "SELECT owner, description, public, tables, indexes, views," \
          " access, created, modified FROM dbs WHERE name=?"
    cursor.execute(sql, (name,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    return {'name':        name,
            'owner':       row[0],
            'description': row[1],
            'public':      bool(row[2]),
            'tables':      json.loads(row[3]),
            'indexes':     json.loads(row[4]),
            'views':       json.loads(row[5]),
            'access':      json.loads(row[6]),
            'created':     row[7],
            'modified':    row[8],
            'size':        os.path.getsize(utils.dbpath(name))}

def create_table(cnx, schema, if_not_exists=False):
    """Create a table given by its schema, in the connected database.
    Raise ValueError if any problem.
    """
    if not schema.get('name'):
        raise ValueError('no table name defined')
    if not constants.NAME_RX.match(schema['name']):
        raise ValueError('invalid table name')
    if not schema.get('columns'):
        raise ValueError('no columns defined')
    names = set()
    for column in schema['columns']:
        if column['name'] in names:
            raise ValueError("column name %s repeated" % column['name'])
        names.add(column['name'])
    # Collect columns forming primary key
    primarykey = []
    for column in schema['columns']:
        if column.get('primarykey'):
            primarykey.append(column['name'])
    # Column definitions, including column constraints
    clauses = []
    for column in schema['columns']:
        coldef = [column['name'], column['type']]
        if column['name'] in primarykey:
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
    sql = "CREATE TABLE %s %s (%s)" % (if_not_exists and 'IF NOT EXISTS' or '',
                                       schema['name'],
                                       ', '.join(clauses))
    cnx.execute(sql)

def create_index(cnx, schema, if_not_exists=False):
    """Create an index given by its schema in the connected database.
    Raise ValueError if any problem.
    """
    if not schema.get('columns'):
        raise ValueError('no columns defined')
    if len(schema['columns']) != len(set(schema['columns'])):
        raise ValueError('same column given more than once')
    sql = ['CREATE']
    if schema.get('unique'):
        sql.append('UNIQUE')
    sql.append('INDEX')
    if if_not_exists:
        sql.append('IF NOT EXISTS')
    sql.append("%s ON %s" % (schema['name'], schema['table']))
    sql.append("(%s)" % ','.join(schema['columns']))
    cnx.execute(' '.join(sql))

def get_cnx(dbname):
    "Get a connection for the given database name."
    try:
        return flask.g.dbcnx[dbname]
    except KeyError:
        # This will be closed by app.finalize
        dbcnx = flask.g.dbcnx[dbname] = sqlite3.connect(utils.dbpath(dbname))
        dbcnx.execute('PRAGMA foreign_keys=ON')
        return dbcnx

def has_read_access(db):
    "Does the current user (if any) have read access to the database?"
    if db['public']: return True
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_read(dbname):
    """Get the database and check that the current user as read access.
    Raise ValueError if any problem.
    """
    db = get_db(dbname)
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

def get_check_write(dbname):
    """Get the database and check that the current user as write access.
    Raise ValueError if any problem.
    """
    db = get_db(dbname)
    if db is None:
        raise ValueError('no such database')
    if not has_write_access(db):
        raise ValueError('may not write to the database')
    return db

def get_nrows(name, dbcnx):
    "Get the number of rows in the table or view."
    cursor = dbcnx.cursor()
    cursor.execute("SELECT COUNT(*) FROM %s" % name)
    return cursor.fetchone()[0]