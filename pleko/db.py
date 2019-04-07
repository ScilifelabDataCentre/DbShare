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

TABLES_TABLE = dict(
    name=constants.TABLES,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='schema', type=constants.TEXT, notnull=True)]
)

INDEXES_TABLE = dict(
    name=constants.INDEXES,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='schema', type=constants.TEXT, notnull=True)]
)

VIEWS_TABLE = dict(
    name=constants.VIEWS,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='schema', type=constants.TEXT, notnull=True)]
)

PLOTS_TABLE = dict(
    name=constants.PLOTS,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='sourcename', type=constants.TEXT, notnull=True),
             dict(name='type', type=constants.TEXT, notnull=True),
             dict(name='spec', type=constants.TEXT, notnull=True)]
)

PLOTS_INDEX = dict(
    name=constants.PLOTS + '_index', 
    table=constants.PLOTS,
    columns=['sourcename'])


blueprint = flask.Blueprint('db', __name__)

@blueprint.route('/<nameext:dbname>', methods=['GET', 'POST', 'DELETE'])
def home(dbname):               # NOTE: dbname is a NameExt instance!
    "List the database tables, views and metadata. Delete the database."
    if utils.is_method_GET():
        try:
            db = get_check_read(str(dbname), nrows=True)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        if dbname.ext is None or dbname.ext == 'html':
            return flask.render_template(
                'db/home.html', 
                db=db,
                has_write_access=has_write_access(db),
                can_change_mode=has_write_access(db, check_mode=False))
        elif dbname.ext == 'json':
            return flask.jsonify(db)
        else:
            flask.abort(406)

    elif utils.is_method_DELETE():
        try:
            db = get_check_write(str(dbname))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        cnx = pleko.master.get_cnx(write=True)
        with cnx:
            sql = 'DELETE FROM dbs_logs WHERE name=?'
            cnx.execute(sql, (str(dbname),))
            sql = 'DELETE FROM dbs WHERE name=?'
            cnx.execute(sql, (str(dbname),))
            os.remove(utils.dbpath(str(dbname)))
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
                sql = get_sql_create_table(TABLES_TABLE)
                ctx.dbcnx.execute(sql)
                sql = get_sql_create_table(INDEXES_TABLE)
                ctx.dbcnx.execute(sql)
                sql = get_sql_create_table(VIEWS_TABLE)
                ctx.dbcnx.execute(sql)
                sql = get_sql_create_table(PLOTS_TABLE)
                ctx.dbcnx.execute(sql)
                sql = get_sql_create_index(PLOTS_INDEX)
                ctx.dbcnx.execute(sql)
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=ctx.db['name']))

@blueprint.route('/<name:dbname>/edit', methods=['GET', 'POST'])
@pleko.user.login_required
def edit(dbname):
    "Edit the database metadata."
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
                print(schema)
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
                 # This does not update the spec data URLs.
                ctx.set_name(flask.request.form['name'])
                ctx.set_description(flask.request.form.get('description'))
                ctx.db['origin']  = dbname # Will show up in logs
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone', dbname=dbname))
        shutil.copy(utils.dbpath(dbname), utils.dbpath(ctx.db['name']))
        pleko.plot.update_spec_data_urls(ctx.db['name'], dbname)
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
                       'public':  False,
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
            # Update existing database entry in master
            if self.old:
                sql = "UPDATE dbs SET owner=?, description=?, public=?," \
                      " readonly=?, modified=? WHERE name=?"
                self.cnx.execute(sql, (self.db['owner'],
                                       self.db.get('description'),
                                       bool(self.db['public']),
                                       bool(self.db['readonly']),
                                       self.db['modified'],
                                       self.db['name']))
            # Create database entry in master, and its Sqlite file
            else:
                try:
                    db = sqlite3.connect(utils.dbpath(self.db['name']))
                except sqlite3.Error as error:
                    raise ValueError(str(error))
                else:
                    db.close()
                sql = "INSERT INTO dbs" \
                      " (name, owner, description, public, readonly," \
                      "  created, modified) VALUES (?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.db['name'],
                                       self.db['owner'],
                                       self.db.get('description'),
                                       bool(self.db['public']),
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
            pleko.plot.update_spec_data_urls(name, oldname)
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
        sql = get_sql_create_table(schema)
        self.dbcnx.execute(sql)
        sql = "INSERT INTO %s (name, schema) VALUES (?, ?)" % constants.TABLES
        with self.dbcnx:
            self.dbcnx.execute(sql, (schema['name'], json.dumps(schema)))
        self.db['tables'][schema['name']] = schema

    def update_table(self, schema):
        "Update the table with the new schema."
        sql = "UPDATE %s SET schema=? WHERE name=?" % constants.TABLES
        with self.dbcnx:
            self.dbcnx.execute(sql, (json.dumps(schema), schema['name']))
        self.db['tables'][schema['name']] = schema

    def delete_table(self, tablename, vacuum=True):
        "Delete the table from the database and from the database definition."
        try:
            self.db['tables'].pop(tablename)
        except KeyError:
            raise ValueError('no such table in database')
        # Delete all indexes for this table.
        for indexname in list(self.db['indexes']):
            self.delete_index(indexname)
        # Delete all plots having this table as source.
        for plot in self.db['plots'].get(tablename, []):
            self.delete_plot(plot['name'])
        # Delete all views having this table as source.
        # Will recursively delete other dependent views and plots.
        for view in list(self.db['views'].values()):
            if tablename in view['sources']:
                # Need to catch KeyError, since recursion might
                # have deleted the view before we get here.
                try:
                    self.delete_view(view['name'])
                except KeyError:
                    pass
        with self.dbcnx:
            sql = "DELETE FROM %s WHERE name=?" % constants.TABLES
            self.dbcnx.execute(sql, (tablename,))
        self.dbcnx.execute("DROP TABLE %s" % tablename)
        if vacuum:
            self.dbcnx.execute('VACUUM')

    def add_index(self, schema):
        "Create an index in the database and add to the database definition."
        if schema['table'] not in self.db['tables']:
            raise ValueError("no such table %s for index %s" % (schema['table'],
                                                                schema['name']))
        if schema['name'] in self.db['indexes']:
            raise ValueError("index %s already defined" % schema['name'])
        sql = get_sql_create_index(schema)
        self.dbcnx.execute(sql)
        sql = "INSERT INTO %s (name, schema) VALUES (?, ?)" % constants.INDEXES
        with self.dbcnx:
            self.dbcnx.execute(sql, (schema['name'], json.dumps(schema)))
        self.db['indexes'][schema['name']] = schema

    def delete_index(self, indexname):
        "Delete an index in the database."
        try:
            self.db['indexes'].pop(indexname)
        except KeyError:
            raise ValueError('no such index in database')
        with self.dbcnx:
            sql = "DELETE FROM %s WHERE name=?" % constants.INDEXES
            self.dbcnx.execute(sql, (indexname,))
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
        sql = "CREATE VIEW %s AS %s" %(schema['name'],
                                       pleko.query.get_sql_query(schema['query']))
        self.dbcnx.execute(sql)
        cursor = self.dbcnx.cursor()
        try:
            sql = "PRAGMA table_info(%s)" % schema['name']
            cursor.execute(sql)
        except sqlite3.Error:   # Invalid view
            sql = "DROP VIEW %s" % schema['name']
            cursor.execute(sql)
            raise ValueError('invalid view; maybe non-existent column?')
        schema['sources'] = [s.strip() for s in schema['query']['from'].split(',')]
        schema['columns'] = [{'name': row[1], 'type': row[2]} for row in cursor]
        sql = "INSERT INTO %s (name, schema) VALUES (?, ?)" % constants.VIEWS
        with self.dbcnx:
            self.dbcnx.execute(sql, (schema['name'], json.dumps(schema)))
        self.db['views'][schema['name']] = schema

    def update_view(self, schema):
        "Update the view with the new schema."
        sql = "UPDATE %s SET schema=? WHERE name=?" % constants.VIEWS
        with self.dbcnx:
            self.dbcnx.execute(sql, (json.dumps(schema), schema['name']))
        self.db['views'][schema['name']] = schema

    def delete_view(self, viewname):
        "Delete a view in the database."
        try:
            self.db['views'].pop(viewname)
        except KeyError:
            raise ValueError('no such view in database')
        # Delete all plots having this view as source.
        for plot in self.db['plots'].get(viewname, []):
            self.delete_plot(plot['name'])
        # Delete all views having this view as a source.
        # Will recursively delete other dependent views and plots.
        for view in list(self.db['views'].values()):
            if viewname in view['sources']:
                # Need to catch KeyError, since recursion might
                # have deleted the view before we get here.
                try:
                    self.delete_view(view['name'])
                except KeyError:
                    pass
        with self.dbcnx:
            sql = "DELETE FROM %s WHERE name=?" % constants.VIEWS
            self.dbcnx.execute(sql, (viewname,))
        self.dbcnx.execute("DROP VIEW %s" % viewname)

    def delete_plot(self, plotname):
        with self.dbcnx:
            sql = "DELETE FROM %s WHERE name=?" % constants.PLOTS
            self.dbcnx.execute(sql, (plotname,))


def get_dbs(public=None, owner=None, complete=False):
    "Get a list of databases according to criteria."
    sql = "SELECT name FROM dbs"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' AND '.join(criteria.keys())
    cursor = pleko.master.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [get_db(row[0], complete=complete) for row in cursor]

def get_db(name, complete=False):
    """Return the database metadata for the given name.
    Return None if no such database.
    """
    cursor = pleko.master.get_cursor()
    sql = "SELECT owner, description, public, readonly," \
          " created, modified FROM dbs WHERE name=?"
    cursor.execute(sql, (name,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    db = {'name':        name,
          'owner':       row[0],
          'description': row[1],
          'public':      bool(row[2]),
          'readonly':    bool(row[3]),
          'created':     row[4],
          'modified':    row[5],
          'size':        os.path.getsize(utils.dbpath(name))}
    if complete:
        cursor = get_cnx(name).cursor()
        sql = "SELECT name, schema FROM %s" % constants.TABLES
        cursor.execute(sql)
        db['tables'] = dict([(row[0], json.loads(row[1])) for row in cursor])
        sql = "SELECT name, schema FROM %s" % constants.INDEXES
        cursor.execute(sql)
        db['indexes'] = dict([(row[0], json.loads(row[1])) for row in cursor])
        sql = "SELECT name, schema FROM %s" % constants.VIEWS
        cursor.execute(sql)
        db['views'] = dict([(row[0], json.loads(row[1])) for row in cursor])
        sql = "SELECT name, sourcename, type, spec FROM %s" % constants.PLOTS
        cursor.execute(sql)
        plots = [{'name': row[0],
                  'sourcename': row[1], 
                  'type': row[2],
                  'spec': json.loads(row[3])} for row in cursor]
        db['plots'] = {}
        for plot in plots:
            db['plots'].setdefault(plot['sourcename'], []).append(plot)
        for sourcename, plotlist in list(db['plots'].items()):
            db['plots'][sourcename] = utils.sorted_schema(plotlist)
    return db

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

def get_schema(db, sourcename):
    """Get the schema of the table or view. 
    Add a member 'type' denoting which it is.
    Raise ValueError if no such table or view.
    """
    try:
        schema = db['tables'][sourcename]
        schema['type'] = constants.TABLE
    except KeyError:
        try:
            schema = db['views'][sourcename]
            schema['type'] = constants.VIEW
        except KeyError:
            raise ValueError('no such table/view')
    return schema

def get_sql_create_table(schema, if_not_exists=False):
    """Return SQL to create a table given by its schema.
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
    sql = ['CREATE TABLE']
    if if_not_exists:
        sql.append('IF NOT EXISTS')
    sql.append(schema['name'])
    sql.append("(%s)" % ', '.join(clauses))
    return ' '.join(sql)

def get_sql_create_index(schema, if_not_exists=False):
    """Return SQL to create an index given by its schema.
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
    return ' '.join(sql)

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

def get_check_read(dbname, nrows=False, complete=True):
    """Get the database and check that the current user as read access.
    Optionally add nrows for each table and view.
    Raise ValueError if any problem.
    """
    db = get_db(dbname, complete=complete)
    if db is None:
        raise ValueError('no such database')
    if not has_read_access(db):
        raise ValueError('may not read the database')
    if nrows:
        set_nrows(db)
    return db

def has_write_access(db, check_mode=True):
    "Does the current user (if any) have write access to the database?"
    if not flask.g.current_user: return False
    if check_mode and db['readonly']: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_write(dbname, check_mode=True, nrows=False, complete=True):
    """Get the database and check that the current user as write access.
    Optionally add nrows for each table and view.
    Raise ValueError if any problem.
    """
    db = get_db(dbname, complete=complete)
    if db is None:
        raise ValueError('no such database')
    if not has_write_access(db, check_mode=check_mode):
        raise ValueError('may not write to the database')
    if nrows:
        set_nrows(db)
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
