"Database HTML endpoints."

import copy
import csv
import hashlib
import io
import itertools
import json
import os
import os.path
import re
import shutil
import sqlite3
import stat
import tarfile
import urllib.parse

import dpath
import flask

import dbshare.system
import dbshare.table
import dbshare.query
import dbshare.user
from dbshare import constants
from dbshare import utils

TABLES_TABLE = dict(
    name=constants.TABLES,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='schema', type=constants.TEXT, notnull=True)],
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

VISUALS_TABLE = dict(
    name=constants.VISUALS,
    columns=[dict(name='name', type=constants.TEXT, primarykey=True),
             dict(name='sourcename', type=constants.TEXT, notnull=True),
             dict(name='spec', type=constants.TEXT, notnull=True)]
)

VISUALS_INDEX = dict(
    name=constants.VISUALS + '_index', 
    table=constants.VISUALS,
    columns=['sourcename'])


blueprint = flask.Blueprint('db', __name__)

@blueprint.route('/<nameext:dbname>')
def display(dbname):
    "List the database tables, views and metadata."
    try:
        db = get_check_read(str(dbname), nrows=True)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if dbname.ext in ('tar', 'tar.gz', 'tar.bz2'):
        try:
            mode = 'w:' + dbname.ext.split('.')[1]
        except IndexError:
            mode = 'w'
        dbcnx = get_cnx(db['name'])
        outfile = io.BytesIO()
        tar = tarfile.open(fileobj=outfile, mode=mode)
        schemas = list(db['tables'].values()) + list(db['views'].values())
        for schema in schemas:
            columns = [c['name'] for c in schema['columns']]
            sql = 'SELECT %s FROM "%s"' % \
                  (','.join([f'"{c}"' for c in columns]), schema['name'])
            writer = utils.CsvWriter(header=columns)
            try:
                cursor = utils.execute_timeout(dbcnx, sql)
            except SystemError:
                pass
            else:
                writer.write_rows(cursor)
                data = writer.getvalue().encode('utf-8')
                tarinfo = tarfile.TarInfo(name=f"{dbname}/{schema['name']}.csv")
                tarinfo.size = len(data)
                tar.addfile(tarinfo, io.BytesIO(data))
        tar.close()
        response = flask.make_response(outfile.getvalue())
        response.headers.set('Content-Type', constants.TAR_MIMETYPE)
        response.headers.set('Content-Disposition', 'attachment', 
                             filename=f"{dbname}.{dbname.ext}")
        return response

    elif dbname.ext in (None, 'html'):
        return flask.render_template(
            'db/display.html', 
            db=db,
            title=db.get('title') or "Database {}".format(dbname),
            has_write_access=has_write_access(db),
            can_change_mode=has_write_access(db, check_mode=False))

    else:
        flask.abort(http.client.NOT_ACCEPTABLE)

@blueprint.route('/', methods=['GET', 'POST'])
@dbshare.user.login_required
def create():
    "Create a database."
    try:
        check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(
            flask.url_for('dbs.owner', 
                          username=flask.g.current_user['username']))

    if utils.http_GET():
        return flask.render_template('db/create.html')

    elif utils.http_POST():
        try:
            with DbContext() as ctx:
                ctx.set_name(flask.request.form['name'])
                ctx.initialize()
                ctx.set_title(flask.request.form.get('title'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create'))
        return flask.redirect(flask.url_for('.display', dbname=ctx.db['name']))

@blueprint.route('/<name:dbname>/edit', methods=['GET', 'POST', 'DELETE'])
@dbshare.user.login_required
def edit(dbname):
    "Edit the database metadata. Or delete the database."
    try:
        db = get_check_write(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.display', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('db/edit.html', db=db)

    elif utils.http_POST():
        try:
            with DbContext(db) as ctx:
                name = flask.request.form.get('name')
                if name:
                    ctx.set_name(name)
                try:
                    ctx.set_title(flask.request.form['title'])
                except KeyError:
                    pass
                try:
                    ctx.set_description(flask.request.form['description'])
                except KeyError:
                    pass
                # Recompute number or rows in tables, while we are at it...
                for schema in ctx.db['tables'].values():
                    ctx.update_table_nrows(schema)
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.display', dbname=db['name']))

    elif utils.http_DELETE():
        try:
            get_check_write(dbname)
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        delete_database(dbname)
        return flask.redirect(
            flask.url_for('dbs.owner',
                          username=flask.g.current_user['username']))

@blueprint.route('/<name:dbname>/logs')
def logs(dbname):
    "Display the logs for a database."
    try:
        db = get_check_read(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    cursor = dbshare.system.get_cursor()
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
@dbshare.user.login_required
def upload(dbname):
    "Create a table from the data in a CSV file."
    try:
        check_quota()
        db = get_check_write(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.display', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('db/upload.html', db=db)

    elif utils.http_POST():
        try:
            csvfile = flask.request.files['csvfile']
            infile = io.StringIO(csvfile.read().decode('utf-8'))
            delimiter = flask.request.form.get('delimiter') or 'comma'
            try:
                delimiter = flask.current_app.config['CSV_FILE_DELIMITERS'][delimiter]['char']
            except KeyError:
                raise ValueError('invalid delimiter')
            nullrepr = flask.request.form.get('nullrepr') or ''
            header = utils.to_bool(flask.request.form.get('header'))
            try:
                tablename = flask.request.form['tablename']
                if not tablename: raise KeyError
            except KeyError:
                tablename = os.path.basename(csvfile.filename)
                tablename = os.path.splitext(tablename)[0]
            with DbContext(db) as ctx:
                tablename, n = ctx.load_csvfile(infile,
                                                tablename,
                                                delimiter=delimiter,
                                                nullrepr=nullrepr,
                                                header=header)
            flask.flash(f"Loaded {n} records.", 'message')
        except (ValueError, IndexError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.upload',
                                                dbname=dbname,
                                                tablename=tablename))
        return flask.redirect(flask.url_for('table.rows',
                                            dbname=dbname,
                                            tablename=tablename))

@blueprint.route('/<name:dbname>/clone', methods=['GET', 'POST'])
@dbshare.user.login_required
def clone(dbname):
    "Create a clone of the database."
    try:
        check_quota()
        db = get_check_read(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('db/clone.html', db=db)

    elif utils.http_POST():
        try:
            with DbContext() as ctx:
                name = flask.request.form['name']
                ctx.set_name(name)
                ctx.set_title(flask.request.form.get('title'))
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone', dbname=dbname))
        shutil.copyfile(utils.dbpath(dbname), utils.dbpath(ctx.db['name']))
        db = get_db(name, complete=True)
        with DbContext(db) as ctx:
            ctx.db['cloned']  = dbname # Will show up in logs
            ctx.update_spec_data_urls(dbname)
        return flask.redirect(flask.url_for('.display', dbname=db['name']))

@blueprint.route('/<name:dbname>/download')
def download(dbname):
    "Download the Sqlite3 database file."
    try:
        db = get_check_read(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    return flask.send_file(utils.dbpath(dbname),
                           mimetype=constants.SQLITE3_MIMETYPE,
                           as_attachment=True)

@blueprint.route('/<name:dbname>/vacuum', methods=['POST'])
@dbshare.user.login_required
def vacuum(dbname):
    "Run VACUUM on the database."
    utils.check_csrf_token()
    try:
        db = get_check_write(dbname) # Do NOT allow if read-only (for hashes)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbcnx = get_cnx(db['name'], write=True)
        sql = 'VACUUM'
        dbcnx.execute(sql)
    except sqlite3.Error as error:
        flask.flash(str(error), 'error')
    return flask.redirect(flask.url_for('.display', dbname=db['name']))

@blueprint.route('/<name:dbname>/analyze', methods=['POST'])
@dbshare.user.login_required
def analyze(dbname):
    "Run ANALYZE on the database."
    utils.check_csrf_token()
    try:
        db = get_check_write(dbname) # Do NOT allow if read-only (for hashes)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbcnx = get_cnx(db['name'], write=True)
        sql = 'ANALYZE'
        dbcnx.execute(sql)
    except sqlite3.Error as error:
        flask.flash(str(error), 'error')
    return flask.redirect(flask.url_for('.display', dbname=db['name']))

@blueprint.route('/<name:dbname>/public', methods=['POST'])
@dbshare.user.login_required
def public(dbname):
    "Set the database to public access."
    utils.check_csrf_token()
    try:
        db = get_check_write(dbname, check_mode=False)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        with DbContext(db) as ctx:
            ctx.set_public(True)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Database set to public access.', 'message')
    return flask.redirect(flask.url_for('.display', dbname=db['name']))

@blueprint.route('/<name:dbname>/private', methods=['POST'])
@dbshare.user.login_required
def private(dbname):
    "Set the database to private access."
    utils.check_csrf_token()
    try:
        db = get_check_write(dbname, check_mode=False)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        with DbContext(db) as ctx:
            ctx.set_public(False)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
    else:
        flask.flash('Database public access revoked.', 'message')
    return flask.redirect(flask.url_for('.display', dbname=db['name']))

@blueprint.route('/<name:dbname>/readwrite', methods=['POST'])
@dbshare.user.login_required
def readwrite(dbname):
    "Set the database to read-write mode."
    utils.check_csrf_token()
    try:
        db = get_check_write(dbname, check_mode=False)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    if db['readonly']:
        try:
            with DbContext(db) as ctx:
                ctx.set_readonly(False)
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        else:
            flask.flash('Database set to read-write mode.', 'message')
    return flask.redirect(flask.url_for('.display', dbname=db['name']))

@blueprint.route('/<name:dbname>/readonly', methods=['POST'])
@dbshare.user.login_required
def readonly(dbname):
    "Set the database to read-only mode. Compute content hashes."
    utils.check_csrf_token()
    try:
        db = get_check_write(dbname, check_mode=False)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    if not db['readonly']:
        try:
            with DbContext(db) as ctx:
                ctx.set_readonly(True)
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        else:
            flask.flash('Database set to read-only mode.', 'message')
    return flask.redirect(flask.url_for('.display', dbname=db['name']))


class DbContext:
    "Context handler to create, modify and save metadata for a database."

    def __init__(self, db=None):
        if db is None:
            self.db = {'owner':    flask.g.current_user['username'],
                       'public':   False,
                       'readonly': False,
                       'hashes':   {},
                       'created':  utils.get_time()}
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
            self._cnx = dbshare.system.get_cnx(write=True)
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
                raise ValueError(f"invalid db: {key} not set")
        self.db['modified'] = utils.get_time()
        with self.cnx:
            # Update the existing database entry in system.
            if self.old:
                # The foreign key from dbs_log to dbs will temporarily be wrong.
                # Switch off enforcing foreign key until updating done.
                sql = 'PRAGMA foreign_keys=OFF'
                self.cnx.execute(sql)
                sql = "UPDATE dbs SET name=?, owner=?, title=?," \
                    "description=?, public=?, readonly=?, modified=?" \
                    " WHERE name=?"
                self.cnx.execute(sql, (self.db['name'],
                                       self.db['owner'],
                                       self.db.get('title'),
                                       self.db.get('description'),
                                       bool(self.db['public']),
                                       bool(self.db['readonly']),
                                       self.db['modified'],
                                       self.old['name']))
                # The Sqlite3 database file was renamed in 'set_name'.
                if self.old.get('name') != self.db['name']:
                    # Fix entries in log records.
                    sql = "UPDATE dbs_logs SET name=? WHERE name=?"
                    self.cnx.execute(sql, (self.db['name'], self.old['name']))
                    # No need to fix hash values: is (or at least, was)
                    # in read/write mode, so db has no hash values.
                # Insert hash values if newly computed.
                if not self.old['hashes'] and self.db['hashes']:
                    sql = "INSERT INTO dbs_hashes (name, hashname, hashvalue)" \
                          " VALUES (?, ?, ?)"
                    for hashname in self.db['hashes']:
                        self.cnx.execute(sql, (self.db['name'],
                                               hashname,
                                               self.db['hashes'][hashname]))
                # Delete hash values if removed.
                elif self.old['hashes'] and not self.db['hashes']:
                    sql = "DELETE FROM dbs_hashes WHERE name=?"
                    self.cnx.execute(sql, (self.db['name'],))
                sql = 'PRAGMA foreign_keys=ON'
                self.cnx.execute(sql)

            # New database.
            else:
                # This actually creates the database file.
                self.dbcnx
                # Create the database entry in system.
                sql = "INSERT INTO dbs" \
                      " (name, owner, title, description, public, readonly," \
                      "  created, modified) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.db['name'],
                                       self.db['owner'],
                                       self.db.get('title'),
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
        # Set the OS-level file permissions.
        if self.db['readonly']:
            os.chmod(utils.dbpath(self.db['name']), stat.S_IREAD)
        else:
            os.chmod(utils.dbpath(self.db['name']), stat.S_IREAD|stat.S_IWRITE)

    def set_name(self, name):
        """Set or change the database name.
        Raise ValueError if name is invalid or already in use.
        """
        assert not hasattr(self, '_dbcnx') # Must be done before any write ops.
        if name == self.db.get('name'): return
        if not constants.NAME_RX.match(name):
            raise ValueError('invalid database name')
        if get_db(name):
            raise ValueError('database name already in use')
        old_dbname = self.db.get('name')
        if old_dbname:
            # Rename the Sqlite3 file if the database already exists.
            os.rename(utils.dbpath(old_dbname), utils.dbpath(name))
            # The entries in the dbs_log will be fixed in '__exit__'
        self.db['name'] = name
        # Update of spec data URLs must be done *after* db rename.
        if old_dbname:
            self.update_spec_data_urls(old_dbname)

    def set_title(self, title):
        "Set the database title."
        self.db['title'] = title or None

    def set_description(self, description):
        "Set the database description."
        self.db['description'] = description or None

    def set_public(self, access):
        "Set to public (True) or private (False) access."
        self.db['public'] = access

    def set_readonly(self, mode):
        """Set to 'readonly' (True) or 'readwrite' (False).
        If 'readonly', then compute the hash values, else remove them.
        """
        if self.db['readonly'] == mode: return
        self.db['readonly'] = self.readonly = mode
        if mode:
            hashes = {}
            for hashname in flask.current_app.config['CONTENT_HASHES']:
                hashes[hashname] = hashlib.new(hashname)
            with open(utils.dbpath(self.db['name']), 'rb') as infile:
                data = infile.read(8192)
                while data:
                    for hash in hashes.values():
                        hash.update(data)
                    data = infile.read(8192)
            for hashname in hashes:
                hashes[hashname] = hashes[hashname].hexdigest()
            self.db['hashes'] = hashes
        else:
            self.db['hashes'] = {}

    def initialize(self):
        "Create the DbShare metadata tables and indexes if they do not exist."
        # Implicitly creates the file, or checks that it is an Sqlite3 file.
        sql = get_sql_create_table(TABLES_TABLE, if_not_exists=True)
        self.dbcnx.execute(sql)
        sql = get_sql_create_table(INDEXES_TABLE, if_not_exists=True)
        self.dbcnx.execute(sql)
        sql = get_sql_create_table(VIEWS_TABLE, if_not_exists=True)
        self.dbcnx.execute(sql)
        sql = get_sql_create_table(VISUALS_TABLE, if_not_exists=True)
        self.dbcnx.execute(sql)
        sql = get_sql_create_index(VISUALS_INDEX, if_not_exists=True)
        self.dbcnx.execute(sql)

    def load_dbfile(self, infile):
        "Load the entire database file present in the given file object."
        with open(utils.dbpath(self.db['name']), 'wb') as outfile:
            outfile.write(infile.read())

    def load_csvfile(self, infile, tablename, 
                     delimiter=',', nullrepr='', header=True):
        """Load the CSV file and infer column types and constraints.
        Return the tablename and the number of records read from the file.
        Raises ValueError or sqlite3.Error if any problem.
        """
        tablename = utils.name_cleaned(tablename)
        tablename = tablename.lower()
        if tablename in self.db['tables']:
            raise ValueError('table name already in use')
        schema = {'name': tablename}

        # Preprocess CSV data; eliminate empty records
        records = [r for r in csv.reader(infile, delimiter=delimiter) if r]
        if not records:
            raise ValueError('empty CSV file')
        if header:
            header = records.pop(0)
            header = [utils.name_cleaned(n) for n in header]
            if len(header) != len(set(header)):
                raise ValueError('non-unique header column names')
        else:
            header = [f"column{i+1}" for i in range(len(records[0]))]

        # Infer column types and constraints
        schema['columns'] = [{'name': name} for name in header]
        try:
            for i, column in enumerate(schema['columns']):
                # First attempt: integer
                column['notnull'] = True
                type = None
                for n, record in enumerate(records):
                    value = record[i]
                    if value == nullrepr:
                        column['notnull'] = False
                    else:
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            break
                else:
                    type = constants.INTEGER
                # Next attempt: float
                if type is None:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value == nullrepr:
                            column['notnull'] = False
                        else:
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                break
                    else:
                        type = constants.REAL
                # Default: text
                if type is None:
                    column['type'] = constants.TEXT
                    if column['notnull']:
                        for record in records:
                            value = record[i]
                            if value == nullrepr:
                                column['notnull'] = False
                                break
                else:
                    column['type'] = type
        except IndexError:
            raise ValueError(f"record {i+1} has too few items")

        # Create the table
        self.add_table(schema)

        # Actually convert values in records
        for i, column in enumerate(schema['columns']):
            type = column['type']
            if type == constants.INTEGER:
                for n, record in enumerate(records):
                    value = record[i]
                    if value == nullrepr:
                        record[i] = None
                    else:
                        record[i] = int(value)
            elif type == constants.REAL:
                for n, record in enumerate(records):
                    value = record[i]
                    if value == nullrepr:
                        record[i] = None
                    else:
                        record[i] = float(value)
            else:
                for n, record in enumerate(records):
                    if record[i] == nullrepr:
                        record[i] = None
        # Insert the data
        sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
              (tablename,
               ','.join(['"%(name)s"' % c for c in schema['columns']]),
               ','.join('?' * len(schema['columns'])))
        with self.dbcnx:
            self.dbcnx.executemany(sql, records)
        self.update_table_nrows(schema)
        return tablename, len(records)

    def update_spec_data_urls(self, old_dbname):
        """When renaming or cloning the database,
        the data URLs of visual specs must be updated.
        """
        old_table_url = utils.url_for('table.rows',
                                      dbname=old_dbname, 
                                      tablename='x')
        old_table_url = old_table_url[:-1]
        new_table_url = utils.url_for('table.rows',
                                      dbname=self.db['name'],
                                      tablename='x')
        new_table_url = new_table_url[:-1]
        old_view_url = utils.url_for('view.rows',
                                     dbname=old_dbname,
                                     viewname='x')
        old_view_url = old_view_url[:-1]
        new_view_url = utils.url_for('view.rows',
                                     dbname=self.db['name'],
                                     viewname='x')
        new_view_url = new_view_url[:-1]
        for visual in [v for visuallist in self.db['visuals'].values()
                       for v in visuallist]:
            spec = visual['spec']
            for path, href in dpath.util.search(spec, 'data/url', yielded=True):
                href = href.replace(old_table_url, new_table_url)
                href = href.replace(old_view_url, new_view_url)
                dpath.util.set(spec, path, href)
            self.update_visual(visual['name'], spec)

    def add_table(self, schema, query=None, create=True):
        """Create the table in the database and add to the database definition.
        If 'query' is given, do 'CREATE TABLE AS', and fix up the schema.
        If 'create' is True, then actually create the table.
        Raises SystemError if the query is interrupted by time-out.
        """
        if not constants.NAME_RX.match(schema['name']):
            raise ValueError('invalid table name')
        schema['name'] = schema['name'].lower()
        if schema['name'] in self.db['tables']:
            raise ValueError('name is already in use for a table')
        if schema['name'] in self.db['views']:
            raise ValueError('name is already in use for a view')
        if query:
            sql = dbshare.query.get_sql_statement(query)
            sql = 'CREATE TABLE "%s" AS %s' % (schema['name'], sql)
            utils.execute_timeout(self.dbcnx, sql)
            if not schema.get('description'):
                schema['description'] = sql
            sql = 'PRAGMA table_info("%s")' % schema['name']
            cursor = self.dbcnx.execute(sql)
            schema['columns'] = [{'name': row[1], 'type': row[2]} 
                                 for row in cursor]
        elif create:
            sql = get_sql_create_table(schema)
            self.dbcnx.execute(sql)
        with self.dbcnx:
            sql = f"INSERT INTO {constants.TABLES} (name,schema) VALUES (?,?)"
            self.dbcnx.execute(sql, (schema['name'], json.dumps(schema)))
        self.update_table_nrows(schema)
        self.db['tables'][schema['name']] = schema

    def update_table(self, schema):
        "Update the table with the new schema."
        sql = f"UPDATE {constants.TABLES} SET schema=? WHERE name=?"
        with self.dbcnx:
            self.dbcnx.execute(sql, (json.dumps(schema), schema['name']))
        self.db['tables'][schema['name']] = schema

    def update_table_nrows(self, schema):
        "Update the number of rows in the table."
        sql = f'''SELECT COUNT(*) FROM "{schema['name']}"'''
        schema['nrows'] = self.dbcnx.execute(sql).fetchone()[0]
        self.update_table(schema)

    def empty_table(self, schema):
        "Empty the table; delete all rows."
        with self.dbcnx:
            sql = f'''DELETE FROM "{schema['name']}"'''
            self.dbcnx.execute(sql)
            self.update_table_nrows(schema)

    def delete_table(self, tablename):
        "Delete the table from the database and from the database definition."
        try:
            self.db['tables'].pop(tablename)
        except KeyError:
            raise ValueError('no such table in database')
        # Delete all indexes for this table.
        for indexname in list(self.db['indexes']):
            self.delete_index(indexname)
        # Delete all visuals having this table as source.
        for visual in self.db['visuals'].get(tablename, []):
            self.delete_visual(visual['name'])
        # Delete all views having this table as source.
        # Will recursively delete other dependent views and visuals.
        for view in list(self.db['views'].values()):
            if tablename in view['sources']:
                # Need to catch KeyError, since recursion might
                # have deleted the view before we get here.
                try:
                    self.delete_view(view['name'])
                except KeyError:
                    pass
        with self.dbcnx:
            sql = 'DELETE FROM "%s" WHERE name=?' % constants.TABLES
            self.dbcnx.execute(sql, (tablename,))
        sql = 'DROP TABLE "%s"' % tablename
        self.dbcnx.execute(sql)
        sql = 'VACUUM'
        self.dbcnx.execute(sql)

    def add_index(self, schema):
        "Create an index in the database and add to the database definition."
        if schema['table'] not in self.db['tables']:
            raise ValueError("no such table %s for index %s" % (schema['table'],
                                                                schema['name']))
        schema['name'] = schema['name'].lower()
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
        sql = 'DROP INDEX "%s"' % indexname
        self.dbcnx.execute(sql)

    def add_view(self, schema, create=True):
        """Create a view in the database and add to the database definition.
        If 'create' is True, then actually create the view.
        """
        if not schema.get('name'):
            raise ValueError('no view name defined')
        schema['name'] = schema['name'].lower()
        if not constants.NAME_RX.match(schema['name']):
            raise ValueError('invalid view name')
        if schema['name'] in self.db['tables']:
            raise ValueError('name is already in use for a table')
        if schema['name'] in self.db['views']:
            raise ValueError('name is already in use for a view')
        if not schema.get('query'):
            raise ValueError('no query statement defined')
        if create:
            sql = 'CREATE VIEW "%s" AS %s' % \
                  (schema['name'],
                   dbshare.query.get_sql_statement(schema['query']))
            self.dbcnx.execute(sql)
        cursor = self.dbcnx.cursor()
        try:
            sql = 'PRAGMA table_info("%s")' % schema['name']
            cursor.execute(sql)
        except sqlite3.Error:   # Invalid view
            sql = 'DROP VIEW "%s"' % schema['name']
            cursor.execute(sql)
            raise ValueError('invalid view; maybe non-existent column?')
        # Source names considering quotes and disregarding AS part, if any.
        schema['sources'] = dbshare.query.get_from_sources(schema['query']['from'])
        schema['columns'] = [{'name': row[1], 'type': row[2]} for row in cursor]
        sql = "INSERT INTO %s (name, schema) VALUES (?,?)" % constants.VIEWS
        with self.dbcnx:
            self.dbcnx.execute(sql, (schema['name'], json.dumps(schema)))
        self.db['views'][schema['name']] = schema

    def update_view(self, schema):
        "Update the view with the new schema."
        with self.dbcnx:
            sql = "UPDATE %s SET schema=? WHERE name=?" % constants.VIEWS
            self.dbcnx.execute(sql, (json.dumps(schema), schema['name']))
        self.db['views'][schema['name']] = schema

    def delete_view(self, viewname):
        "Delete a view in the database."
        try:
            self.db['views'].pop(viewname)
        except KeyError:
            raise ValueError('no such view in database')
        # Delete all visuals having this view as source.
        for visual in self.db['visuals'].get(viewname, []):
            self.delete_visual(visual['name'])
        # Delete all views having this view as a source.
        # Will recursively delete other dependent views and visuals.
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
        sql = 'DROP VIEW "%s"' % viewname
        self.dbcnx.execute(sql)

    def add_visual(self, visualname, sourcename, spec):
        "Add the visualization for the given source (table or view)."
        sql = "INSERT INTO %s (name, sourcename, spec)" \
              " VALUES (?, ?, ?)" % constants.VISUALS
        with self.dbcnx:
            self.dbcnx.execute(sql, (visualname.lower(),
                                     sourcename,
                                     json.dumps(spec)))

    def update_visual(self, visualname, spec, new_visualname=None):
        "Update the visualization for the given source (table or view)."
        if new_visualname is None:
            new_visualname = visualname
        with self.dbcnx:
            sql = "UPDATE %s SET name=?,spec=? WHERE name=?" % constants.VISUALS
            self.dbcnx.execute(sql,(new_visualname.lower(),
                                    json.dumps(spec),
                                    visualname.lower()))

    def delete_visual(self, visualname):
        "Delete the visualization for the given source (table or view)."
        with self.dbcnx:
            sql = "DELETE FROM %s WHERE name=?" % constants.VISUALS
            self.dbcnx.execute(sql, (visualname.lower(),))

    def check_metadata(self):
        """Check the validity of the metadata for the database.
        Fix the data URLs in the visuals.
        Return False if no metadata (i.e. not a DbShare file), else True.
        Raises ValueError or sqlite3.Error if any problem.
        """
        sql = f"SELECT COUNT(*) FROM {constants.TABLES}"
        if self.dbcnx.execute(sql).fetchone()[0] == 0:
            return False # No metadata; skip.
        sql = f"SELECT name FROM {constants.TABLES}"
        tables1 = [r[0].lower() for r in self.dbcnx.execute(sql)]
        sql = "SELECT name FROM sqlite_master WHERE type=?"
        tables2 = [r[0].lower() for r in self.dbcnx.execute(sql, ('table',))]
        # Do not consider metadata tables and sqlite statistics tables, if any.
        tables2 = [n for n in tables2 if not n.startswith('_')]
        tables2 = [n for n in tables2 if not n.startswith('sqlite_')]
        if set(tables1) != set(tables2):
            raise ValueError('corrupt metadata in DbShare Sqlite3 file')
        # Does the index metatable exist?
        sql = f"SELECT name, schema FROM {constants.INDEXES}"
        self.dbcnx.execute(sql)
        # Does the views metatable exist?
        sql = f"SELECT name, schema FROM {constants.VIEWS}"
        self.dbcnx.execute(sql)
        # Fix the data URLs in the visuals.
        sql = f"SELECT name, spec FROM {constants.VISUALS}"
        visuals = [{'name': row[0], 'spec': json.loads(row[1])}
                   for row in self.dbcnx.execute(sql)]
        # Update the data URLs in the visuals.
        new_root = utils.url_for('home').rstrip('/')
        # Identify the old URL root from a data url in a visual spec.
        old_root = None
        search = dpath.util.search
        for visual in visuals:
            for path,href in search(visual['spec'],'data/url',yielded=True):
                parts = urllib.parse.urlparse(href)
                old_root = urllib.parse.urlunparse(parts[0:2]+('','','',''))
                break
        rx_table = re.compile(r'^.*/table/(.+)/.+$')
        rx_view  = re.compile(r'^.*/view/(.+)/.+$')
        for visual in visuals:
            for path,href in search(visual['spec'],'data/url',yielded=True):
                # Next, replace old URL root with new.
                href = href.replace(old_root, new_root)
                # And, old database name with new in URL path.
                for m in [rx_table.match(href), rx_view.match(href)]:
                    if m:
                        href = href[: m.start(1)] + \
                               self.db['name'] + \
                               href[m.end(1) :]
                        dpath.util.set(visual['spec'], path, href)
                        break
        with self.dbcnx:
            sql = f"UPDATE {constants.VISUALS} SET spec=? WHERE name=?"
            for visual in visuals:
                self.dbcnx.execute(sql, (json.dumps(visual['spec']),
                                         visual['name']))
        return True

    def infer_metadata(self):
        "Infer and save the metadata for the database."
        cursor = self.dbcnx.cursor()
        # Get the table names.
        sql = "SELECT name FROM sqlite_master WHERE type=?"
        cursor.execute(sql, ('table',))
        tablenames = [row[0] for row in cursor 
                      if not row[0].startswith('_')] # Ignore metadata tables.
        # Check the DbShare validity of the table names.
        for tablename in tablenames:
            if not constants.NAME_RX.match(tablename):
                raise ValueError(f"invalid table name '{tablename}' for DbShare")
        # Infer the schema for the tables, and set the metadata.
        for tablename in tablenames:
            schema = {'name': tablename, 'columns': []}
            sql = f'PRAGMA table_info("{tablename}")'
            cursor.execute(sql)
            for row in cursor:
                column = {'name': row[1].lower(), 
                          'type': row[2].upper(),
                          'notnull': bool(row[3]),
                          'primarykey': bool(row[5])}
                schema['columns'].append(column)
            self.add_table(schema, create=False)
        # Get the views, attempt to parse their SQL definitions, and add.
        sql = "SELECT name, sql FROM sqlite_master WHERE type=?"
        cursor.execute(sql, ('view',))
        viewdata = [(row[0], row[1]) for row in cursor]
        for viewname, sql in viewdata:
            schema = {'name': viewname,
                      'title': None,
                      'description': None}
            schema['query'] = query = {}
            try:
                utils.lexer(sql)
                utils.lexer.get_expected('RESERVED', value='CREATE')
                utils.lexer.get_expected('RESERVED', value='VIEW')
                utils.lexer.get_expected('IDENTIFIER')
                utils.lexer.get_expected('RESERVED', value='AS')

                parts = utils.lexer.split_reserved(['SELECT', 'FROM', 'WHERE',
                                                    'ORDER', 'BY', 'LIMIT',
                                                    'OFFSET'])

                query['select'] = ''.join([t['raw'] for t in parts['SELECT']]).strip()
                query['columns'] = dbshare.query.get_select_columns(query['select'])
                query['from'] = ''.join([t['raw'] for t in parts['FROM']]).strip()
                query['where'] = ''.join([t['raw'] for t in parts['WHERE']]).strip()
                try:
                    query['orderby'] = ''.join([t['raw'] for t in parts['BY']]).strip()
                except KeyError:
                    pass
                try:
                    query['limit'] = parts['LIMIT'][0]
                    query['offset'] = parts['OFFSET'][0]
                except KeyError:
                    query['limit'] = None
                    query['offset'] = None
                self.add_view(schema, create=False)
            except (KeyError, ValueError, IndexError, TypeError) as error:
                print(error)
                # Get rid of uninterpretable view.
                sql = f"DROP VIEW {viewname}"
                cursor.execute(sql)
        # Delete all indexes; currently not parsed and may interfere.
        sql = "SELECT name FROM sqlite_master WHERE type=?"
        cursor.execute(sql, ('index',))
        indexnames = [row[0] for row in cursor]
        # Do not attempt to delete Sqlite3 indexes, or visuals index.
        indexnames = [n for n in indexnames 
                      if not n.startswith('sqlite_autoindex')]
        indexnames = [n for n in indexnames if not n.startswith('_')]
        for name in indexnames:
            sql = f"DROP INDEX {name}"
            cursor.execute(sql)

def get_db(name, complete=False):
    """Return the database metadata for the given name.
    Return None if no such database.
    """
    cursor = dbshare.system.get_cursor()
    sql = "SELECT owner, title, description, public, readonly," \
          " created, modified FROM dbs WHERE name=?"
    cursor.execute(sql, (name,))
    rows = cursor.fetchall()
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    db = {'name':       name,
          'owner':      row[0],
          'title':      row[1],
          'description':row[2],
          'public':     bool(row[3]),
          'readonly':   bool(row[4]),
          'created':    row[5],
          'modified':   row[6],
          'size':       os.path.getsize(utils.dbpath(name))}
    db['hashes'] = {}
    sql = "SELECT hashname, hashvalue FROM dbs_hashes WHERE name=?"
    cursor.execute(sql, (name,))
    for row in cursor:
        db['hashes'][row[0]] = row[1]
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
        sql = "SELECT name, sourcename, spec FROM %s" % constants.VISUALS
        cursor.execute(sql)
        visuals = [{'name': row[0],
                  'sourcename': row[1], 
                  'spec': json.loads(row[2])} for row in cursor]
        db['visuals'] = {}
        for visual in visuals:
            db['visuals'].setdefault(visual['sourcename'], []).append(visual)
        for sourcename, visuallist in list(db['visuals'].items()):
            db['visuals'][sourcename] = utils.sorted_schema(visuallist)

        sql = "SELECT name, sourcename, spec FROM %s" % constants.VISUALS
        cursor.execute(sql)
        visuals = [{'name': row[0],
                    'sourcename': row[1], 
                    'spec': json.loads(row[2])} for row in cursor]
        db['visuals'] = {}
        for visual in visuals:
            db['visuals'].setdefault(visual['sourcename'], []).append(visual)
        for sourcename, visuallist in list(db['visuals'].items()):
            db['visuals'][sourcename] = utils.sorted_schema(visuallist)
    return db

def get_usage(username=None):
    "Return the number and total size of the databases for the user, or all."
    cursor = dbshare.system.get_cursor()
    if username:
        sql = "SELECT name FROM dbs WHERE owner=?"
        cursor.execute(sql, (username,))
    else:
        sql = "SELECT name FROM dbs"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return (len(rows),
            sum([os.path.getsize(utils.dbpath(row[0])) for row in rows]))

def check_quota(user=None, size=0):
    "Raise ValueError if the current user has exceeded her size quota."
    if user is None:
        user = flask.g.current_user
    quota = user['quota']
    total_size = get_usage(user['username'])[1] + size
    if quota is not None and total_size > quota:
        raise ValueError('size quota exceeded; cannot add data')

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

def get_visual(db, visualname):
    # db['visuals'] has source name as key and visual lists as values.
    for visual in itertools.chain.from_iterable(db['visuals'].values()):
        if visual['name'] == visualname: return visual
    raise ValueError('no such visual')

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
        coldef = ['"%s" %s' % (column['name'], column['type'])]
        if column['name'] in primarykey:
            column['notnull'] = True
            if len(primarykey) == 1:
                coldef.append('PRIMARY KEY')
        if column.get('notnull'):
            coldef.append('NOT NULL')
        clauses.append(' '.join(coldef))
    # Primary key
    if len(primarykey) >= 2:
        clauses.append('PRIMARY KEY (%s)' %
                       ','.join(['"%s"' for k in primarykey]))
    # Foreign keys
    for foreignkey in schema.get('foreignkeys', []):
        clauses.append('FOREIGN KEY (%s) REFERENCES "%s" (%s)' %
                       (','.join(['"%s"' % c for c in foreignkey['columns']]),
                        foreignkey['ref'],
                        ','.join(['"%s"'%c for c in foreignkey['refcolumns']])))
    sql = ['CREATE TABLE']
    if if_not_exists:
        sql.append('IF NOT EXISTS')
    sql.append('"%s"' % schema['name'])
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
    sql.append('"%s" ON "%s"' % (schema['name'], schema['table']))
    sql.append("(%s)" % ','.join(['"%s"' % c for c in schema['columns']]))
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
        flask.g.dbcnx = utils.get_cnx(utils.dbpath(dbname), write=write)
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
    """Get the database and check that the current user has read access.
    Optionally add nrows for each table and view.
    Raise KeyError if no such database.
    Raise ValueError if may not access.
    """
    db = get_db(dbname, complete=complete)
    if db is None:
        raise KeyError('no such database')
    if not has_read_access(db):
        raise ValueError('may not read the database')
    set_nrows(db, targets=nrows)
    return db

def has_write_access(db, check_mode=True):
    "Does the current user (if any) have write access to the database?"
    if not flask.g.current_user: return False
    if check_mode and db['readonly']: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == db['owner']

def get_check_write(dbname, check_mode=True, nrows=False, complete=True):
    """Get the database and check that the current user has write access.
    Optionally add nrows for each table and view.
    Raise KeyError if no such database.
    Raise ValueError if may not access.
    """
    db = get_db(dbname, complete=complete)
    if db is None:
        raise KeyError('no such database')
    if not has_write_access(db, check_mode=check_mode):
        raise ValueError('may not write to the database')
    set_nrows(db, targets=nrows)
    return db

def set_nrows(db, targets):
    "Set the item 'nrows' for all or given tables and views of the database."
    if not targets: return
    if targets == True:
        targets = list(db['views'].values())
    else:
        targets = [get_schema(db, name) for name in targets]
    cnx = get_cnx(db['name'])
    for target in targets:
        try:
            utils.execute_timeout(cnx, _set_nrows, target=target)
        except SystemError:
            target['nrows'] = None

def _set_nrows(cnx, target):
    "Actually set the nrow values for the given target; executed with time-out."
    sql = 'SELECT COUNT(*) FROM "%s"' % target['name']
    target['nrows'] = cnx.execute(sql).fetchone()[0]

def add_database(dbname, infile, modify_dbname=False, size=0):
    """Add the database file present in the given open file object.
    If the database has the metadata of a DbShare Sqlite3 database, check it.
    Else if the database appears to be a plain Sqlite3 database,
    infer the DbShare metadata from it by inspection.
    If 'modify_name' is True, then attempt to fix a non-unique name.
    'size' should be the size of the database file, if known.
    Return the database dictionary.
    Raise ValueError if any problem.
    """
    try:
        check_quota(size=size)
        with DbContext() as ctx:
            try:
                ctx.set_name(dbname)
            except ValueError:
                if not modify_dbname: raise
                for n in range(1, 1000):
                    try:
                        modified_dbname = f"{dbname}-{n}"
                        ctx.set_name(modified_dbname)
                    except ValueError:
                        pass
                    else:
                        dbname = modified_dbname
                        break
                else:
                    raise ValueError('could not set database name')
            ctx.load_dbfile(infile)
            ctx.initialize()
    except (ValueError, TypeError, OSError, IOError, sqlite3.Error) as error:
        raise ValueError(str(error))
    try:
        with DbContext(get_db(dbname, complete=True)) as ctx: # Re-read db dict
            if not ctx.check_metadata():
                ctx.infer_metadata()
        return ctx.db
    except (ValueError, TypeError, sqlite3.Error) as error:
        delete_database(dbname)
        raise ValueError(str(error))

def delete_database(dbname):
    "Delete the database in the system database and from disk."
    cnx = dbshare.system.get_cnx(write=True)
    with cnx:
        sql = 'DELETE FROM dbs_logs WHERE name=?'
        cnx.execute(sql, (dbname,))
        sql = 'DELETE FROM dbs WHERE name=?'
        cnx.execute(sql, (dbname,))
    try:
        os.remove(utils.dbpath(dbname))
    except FileNotFoundError:
        pass
