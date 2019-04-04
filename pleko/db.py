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
import pleko.plot
import pleko.query
import pleko.user
from pleko import constants
from pleko import utils

PLOT_TABLE = dict(
    name=constants.PLOT_TABLE_NAME,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='tableviewname', type=constants.TEXT, notnull=True),
             dict(name='type', type=constants.TEXT, notnull=True),
             dict(name='spec', type=constants.TEXT, notnull=True)]
)

PLOT_INDEX = dict(name=constants.PLOT_TABLE_NAME + '_index', 
                  table=constants.PLOT_TABLE_NAME,
                  columns=['tableviewname'])

blueprint = flask.Blueprint('db', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'POST', 'DELETE'])
def home(dbname):
    "Display the database tables, views and metadata. Delete the database."
    if utils.is_method_GET():
        try:
            db = get_check_read(dbname, nrows=True, plots=True)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        return flask.render_template(
            'db/home.html', 
            db=db,
            has_write_access=has_write_access(db),
            can_change_mode=has_write_access(db, check_mode=False))

    elif utils.is_method_DELETE():
        try:
            db = get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        cnx = pleko.master.get_cnx(write=True)
        with cnx:
            sql = 'DELETE FROM dbs_logs WHERE name=?'
            cnx.execute(sql, (dbname,))
            sql = 'DELETE FROM dbs WHERE name=?'
            cnx.execute(sql, (dbname,))
            os.remove(utils.dbpath(dbname))
        return flask.redirect(
            flask.url_for('owner', username=flask.g.current_user['username']))

@blueprint.route('/', methods=['GET', 'POST'])
@pleko.user.login_required
def create():
    "Create a database."
    try:
        check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(
            flask.url_for('owner', username=flask.g.current_user['username']))

    if utils.is_method_GET():
        return flask.render_template('db/create.html')

    elif utils.is_method_POST():
        try:
            with DbContext() as ctx:
                ctx.set_name(flask.request.form['name'])
                ctx.set_description(flask.request.form.get('description'))
                create_table(ctx.dbcnx, PLOT_TABLE)
                create_index(ctx.dbcnx, PLOT_INDEX)
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=ctx.db['name']))

@blueprint.route('/<name:dbname>/edit', methods=['GET', 'POST'])
@pleko.user.login_required
def edit(dbname):
    "Edit the database; name, description, access, mode."
    try:
        db = get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('db/edit.html', db=db)

    elif utils.is_method_POST():
        try:
            with DbContext(db) as ctx:
                try:
                    ctx.set_description(flask.request.form['description'])
                except KeyError:
                    pass
                try:
                    ctx.set_name(flask.request.form['name'])
                except KeyError:
                    pass
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=db['name']))

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
    return flask.render_template('db/logs.html', db=db, logs=logs)

@blueprint.route('/<name:dbname>/upload', methods=['GET', 'POST'])
@pleko.user.login_required
def upload(dbname):
    "Create a table from the data in a CSV file."
    try:
        check_quota()
        db = get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('db/upload.html', db=db)

    elif utils.is_method_POST():
        try:
            header = utils.to_bool(flask.request.form.get('header'))
            csvfile = flask.request.files['csvfile']
            try:
                tablename = flask.request.form['tablename']
                if not tablename: raise KeyError
            except KeyError:
                tablename = os.path.basename(csvfile.filename)
                tablename = os.path.splitext(tablename)[0]
                tablename = list(tablename)
                for pos, char in enumerate(tablename):
                    if char not in constants.NAME_CHARS:
                        tablename[pos] = '_'
                tablename = ''.join(tablename)
            if tablename in db['tables']:
                raise ValueError('table name already in use')
            schema = {'name': tablename}

            # Preprocess CSV data
            lines = csvfile.read().decode('utf-8').split('\n')
            records = list(csv.reader(lines))
            # Eliminate empty records
            records = [r for r in records if r]
            if not records:
                raise ValueError('empty CSV file')
            if header:
                header = records.pop(0)
                if len(header) == 0:
                    raise ValueError('empty header record in the CSV file')
                for name in header:
                    if not constants.NAME_RX.match(name):
                        raise ValueError('invalid header column name')
                if len(header) != len(set(header)):
                    raise ValueError('non-unique header column names')
            else:
                header = ["column%i" % (i+1) for i in range(len(records[0]))]

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
            dbcnx = get_cnx(db['name'], write=True)
            cursor = dbcnx.cursor()
            with dbcnx:
                sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                      (tablename,
                       ','.join([c['name'] for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                cursor.executemany(sql, records)
            flask.flash("Inserted %s rows" % len(records), 'message')

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
        check_quota()
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


@blueprint.route('/<name:dbname>/public', methods=['POST'])
@pleko.user.login_required
def public(dbname):
    "Set the database to public access."
    try:
        db = get_check_write(dbname, check_mode=False)
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
        db = get_check_write(dbname, check_mode=False)
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

@blueprint.route('/<name:dbname>/readwrite', methods=['POST'])
@pleko.user.login_required
def readwrite(dbname):
    "Set the database to read-write mode."
    try:
        db = get_check_write(dbname, check_mode=False)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        with DbContext(db) as ctx:
            ctx.db['readonly'] = False
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Database set to read-write mode.', 'message')
    return flask.redirect(flask.url_for('.home', dbname=db['name']))

@blueprint.route('/<name:dbname>/readonly', methods=['POST'])
@pleko.user.login_required
def readonly(dbname):
    "Set the database to read-only mode."
    try:
        db = get_check_write(dbname, check_mode=False)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        with DbContext(db) as ctx:
            ctx.db['readonly'] = True
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Database set to read-only mode.', 'message')
    return flask.redirect(flask.url_for('.home', dbname=db['name']))


class DbContext:
    "Context handler to create, modify and save metadata for a database."

    def __init__(self, db=None):
        if db is None:
            self.db = {'owner':   flask.g.current_user['username'],
                       'tables':  {}, # Key: tablename
                       'indexes': {}, # Key: indexname
                       'views':   {}, # Key: viewname
                       'public':  False,
                       'access':  {},
                       'readonly': False,
                       'created': utils.get_time()}
            self.old = {}
        else:
            self.db = db
            self.old = copy.deepcopy(db)

    @property
    def cnx(self):
        try:
            return self._cnx
        except AttributeError:
            # Don't close connection at exit; done externally to the context
            self._cnx = pleko.master.get_cnx(write=True)
            return self._cnx

    @property
    def dbcnx(self):
        try:
            return self._dbcnx
        except AttributeError:
            # Don't close connection at exit; done externally to the context
            self._dbcnx = get_cnx(self.db['name'], write=True)
            return self._dbcnx

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['name', 'owner']:
            if not self.db.get(key):
                raise ValueError("invalid db: %s not set" % key)
        self.db['modified'] = utils.get_time()
        if not self.old and get_db(self.db['name']):
            raise ValueError('database name already in use')
        with self.cnx:
            # Update existing database in master
            if self.old:
                sql = "UPDATE dbs SET owner=?, description=?," \
                      " tables=?, indexes=?, views=?, public=?, access=?," \
                      " readonly=?, modified=?" \
                      " WHERE name=?"
                self.cnx.execute(sql, (self.db['owner'],
                                       self.db.get('description'),
                                       json.dumps(self.db['tables']),
                                       json.dumps(self.db['indexes']),
                                       json.dumps(self.db['views']),
                                       bool(self.db['public']),
                                       json.dumps(self.db['access']),
                                       bool(self.db['readonly']),
                                       self.db['modified'],
                                       self.db['name']))
            # Create database in master, and Sqlite file
            else:
                try:
                    db = sqlite3.connect(utils.dbpath(self.db['name']))
                except sqlite3.Error as error:
                    raise ValueError(str(error))
                else:
                    db.close()
                sql = "INSERT INTO dbs" \
                      " (name, owner, description, tables, indexes, views," \
                      "  public, access, readonly, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.db['name'],
                                       self.db['owner'],
                                       self.db.get('description'),
                                       json.dumps(self.db['tables']),
                                       json.dumps(self.db['indexes']),
                                       json.dumps(self.db['views']),
                                       bool(self.db['public']),
                                       json.dumps(self.db['access']),
                                       bool(self.db['readonly']),
                                       self.db['created'], 
                                       self.db['modified']))
            # Add log entry
            new = {}
            for key, value in self.db.items():
                if value != self.old.get(key):
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
        assert not hasattr(self, '_dbcnx')
        if name == self.db.get('name'): return
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
        if not constants.NAME_RX.match(schema['name']):
            raise ValueError('invalid table name')
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
        with self.dbcnx:
            self.dbcnx.execute("DELETE FROM plot$ WHERE tableviewname=?",
                               (tablename,))
        self.dbcnx.execute("DROP TABLE %s" % tablename)
        self.dbcnx.execute('VACUUM')

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
        cursor = self.dbcnx.cursor()
        sql = "CREATE VIEW %s AS %s" % (schema['name'], query)
        cursor.execute(sql)
        sql = "PRAGMA table_info(%s)" % schema['name']
        cursor.execute(sql)
        schema['columns'] = [{'name': row[1], 'type': row[2]} for row in cursor]
        self.db['views'][schema['name']] = schema

    def delete_view(self, viewname):
        "Delete a view in the database."
        try:
            self.db['views'].pop(viewname)
        except KeyError:
            raise ValueError('no such view in database')
        with self.dbcnx:
            self.dbcnx.execute("DELETE FROM plot$ WHERE tableviewname=?",
                               (viewname,))
            self.dbcnx.execute("DROP VIEW %s" % viewname)


# Utility functions

def get_dbs(public=None, owner=None):
    "Get a list of databases according to criteria. Does not get database size."
    sql = "SELECT name, owner, description, tables, indexes, views," \
          " public, access, readonly, created, modified FROM dbs"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' AND '.join(criteria.keys())
    cursor = pleko.master.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    result = [{'name':        row[0],
               'owner':       row[1],
               'description': row[2],
               'tables':      json.loads(row[3]),
               'indexes':     json.loads(row[4]),
               'views':       json.loads(row[5]),
               'public':      bool(row[6]),
               'access':      json.loads(row[7]),
               'readonly':    bool(row[8]),
               'created':     row[9],
               'modified':    row[10]}
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
    sql = "SELECT owner, description, tables, indexes, views," \
          " public, access, readonly, created, modified FROM dbs WHERE name=?"
    cursor.execute(sql, (name,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    return {'name':        name,
            'owner':       row[0],
            'description': row[1],
            'tables':      json.loads(row[2]),
            'indexes':     json.loads(row[3]),
            'views':       json.loads(row[4]),
            'public':      bool(row[5]),
            'access':      json.loads(row[6]),
            'readonly':    bool(row[7]),
            'created':     row[8],
            'modified':    row[9],
            'size':        os.path.getsize(utils.dbpath(name))}

def get_usage(username=None):
    "Return the number and total size of the databases for the user, or all."
    cursor = pleko.master.get_cursor()
    if username:
        sql = "SELECT name FROM dbs WHERE owner=?"
        cursor.execute(sql, (username,))
    else:
        sql = "SELECT name FROM dbs"
        cursor.execute(sql)
    rows = list(cursor)
    return (len(rows),
            sum([os.path.getsize(utils.dbpath(row[0])) for row in rows]))

def check_quota(user=None):
    "Raise ValueError if the current user has exceeded her size quota."
    if user is None:
        user = flask.g.current_user
    quota = user['quota']
    if quota is not None and get_usage(user['username'])[1] > quota:
        raise ValueError('you have exceeded your size quota;'
                         ' no more data can be added')

def get_schema(db, tableviewname):
    """Get the schema of the table or view. 
    Add a member 'type' denoting which it is.
    Raise ValueError if no such table or view.
    """
    try:
        schema = db['tables'][tableviewname]
        schema['type'] = 'table'
    except KeyError:
        try:
            schema = db['views'][tableviewname]
            schema['type'] = 'view'
        except KeyError:
            raise ValueError('no such table/view')
    return schema

def create_table(dbcnx, schema, if_not_exists=False):
    """Create a table given by its schema, in the connected database.
    Raise ValueError if any problem.
    """
    if not schema.get('name'):
        raise ValueError('no table name defined')
    if not schema.get('columns'):
        raise ValueError('no columns defined')
    names = set()
    for column in schema['columns']:
        column['name'] = column['name'].lower()
        if column['name'] in names:
            raise ValueError("column name %s repeated" % column['name'])
        if column['name'] == 'rowid':
            raise ValueError("column name 'rowid' is reserved by the system")
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
    dbcnx.execute(sql)

def create_index(dbcnx, schema, if_not_exists=False):
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
    dbcnx.execute(' '.join(sql))

def get_cnx(dbname, write=False):
    """Get a connection for the given database name.
    IMPORTANT: Currently, only one connection to a given database can
    be open at any time!
    If write is true, then assume the old connection is read-only,
    so close it and open a new one.
    """
    if write:
        try:
            flask.g.dbcnx.close()
        except AttributeError:
            pass
        flask.g.dbcnx = utils.get_cnx(utils.dbpath(dbname), write=True)
    try:
        return flask.g.dbcnx
    except AttributeError:
        flask.g.dbcnx = utils.get_cnx(utils.dbpath(dbname))
        return flask.g.dbcnx

def has_read_access(db):
    "Does the current user (if any) have read access to the database?"
    if db['public']: return True
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_read(dbname, nrows=False, plots=False):
    """Get the database and check that the current user as read access.
    Optionally add nrows for each table and view, and plots for database.
    Raise ValueError if any problem.
    """
    db = get_db(dbname)
    if db is None:
        raise ValueError('no such database')
    if not has_read_access(db):
        raise ValueError('may not read the database')
    if nrows:
        set_nrows(db)
    if plots:
        db['plots'] = pleko.plot.get_plots(dbname)
    return db

def has_write_access(db, check_mode=True):
    "Does the current user (if any) have write access to the database?"
    if not flask.g.current_user: return False
    if check_mode and db['readonly']: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_write(dbname, check_mode=True, nrows=False, plots=False):
    """Get the database and check that the current user as write access.
    Raise ValueError if any problem.
    """
    db = get_db(dbname)
    if db is None:
        raise ValueError('no such database')
    if not has_write_access(db, check_mode=check_mode):
        raise ValueError('may not write to the database')
    if nrows:
        set_nrows(db)
    if plots:
        db['plots'] = pleko.plot.get_plots(dbname)
    return db

def set_nrows(db):
    "Set the item 'nrows' in each table and view of the database."
    dbcnx = get_cnx(db['name'])
    for table in db['tables'].values():
        table['nrows'] = get_nrows(table['name'], dbcnx)
    for view in db['views'].values():
        view['nrows'] = get_nrows(view['name'], dbcnx)

def get_nrows(name, dbcnx):
    "Get the number of rows in the table or view."
    cursor = dbcnx.cursor()
    cursor.execute("SELECT COUNT(*) FROM %s" % name)
    return cursor.fetchone()[0]
