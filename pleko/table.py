"Pleko table endpoints."

import csv
import sqlite3

import flask

import pleko.db
import pleko.master
from pleko import constants
from pleko import utils
from pleko.user import login_required

def get_schema(tableid, cursor):
    """Get the schema for the given table given the cursor for the database.
    Raise ValueError if no such table."""
    sql = 'PRAGMA table_info("%s")' % tableid
    cursor.execute(sql)
    rows = list(cursor)
    if len(rows) == 0:
        raise ValueError('no such table in database')
    return {'id': tableid,
            'columns': [{'id': row[1],
                         'type': row[2],
                         'notnull': bool(row[3]),
                         'defaultvalue': row[4],
                         'primarykey': bool(row[5])}
                        for row in rows]}

def get_nrows(tableid, cursor):
    "Get the number of rows in the table."
    cursor.execute("SELECT COUNT(*) FROM %s" % tableid)
    return cursor.fetchone()[0]

def create_table(schema, cursor):
    "Create the table according to the schema."
    clauses = []
    primarykey = []
    for column in schema['columns']:
        if column.get('primarykey'):
            primarykey.append(column['id'])
    for column in schema['columns']:
        coldef = "{id} {type}".format(**column)
        if column['id'] in primarykey:
            column['notnull'] = True
        if column['notnull']:
            coldef += ' NOT NULL'
        clauses.append(coldef)
    if primarykey:
        clauses.append("PRIMARY KEY (%s)" % ','.join(primarykey))
    sql = "CREATE TABLE %s (%s)" % (schema['id'], ', '.join(clauses))
    # XXX
    print(sql)
    cursor.execute(sql)


blueprint = flask.Blueprint('table', __name__)

@blueprint.route('/<id:dbid>', methods=["GET", "POST"])
@login_required
def create(dbid):
    "Create a table with columns in the database."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))

    if utils.is_method_GET():
        return flask.render_template('table/create.html', db=db)

    elif utils.is_method_POST():
        try:
            cnx = pleko.db.get_cnx(dbid)
            schema = {'id': flask.request.form.get('id')}
            if not schema['id']:
                raise ValueError('no table identifier given')
            if not constants.IDENTIFIER_RX.match(schema['id']):
                raise ValueError('invalid table identifier')
            cursor = cnx.cursor()
            sql = "SELECT COUNT(*) FROM sqlite_master WHERE name=?"
            cursor.execute(sql, (schema['id'],))
            if cursor.fetchone()[0] != 0:
                raise ValueError('table identifier already in use')
            ids = set()
            schema['columns'] = []
            for n in range(flask.current_app.config['TABLE_INITIAL_COLUMNS']):
                id = flask.request.form.get("column%sid" % n)
                if not id: break
                if not constants.IDENTIFIER_RX.match(id):
                    raise ValueError("invalid identifier in column %s" % (n+1))
                if id in ids:
                    raise ValueError("repeated identifier in column %s" % (n+1))
                ids.add(id)
                column = {'id': id}
                type = flask.request.form.get("column%stype" % n)
                if type not in constants.COLUMN_TYPES:
                    raise ValueError("invalid type in column %s" % (n+1))
                column['type'] = type
                column['primarykey'] = utils.to_bool(
                    flask.request.form.get("column%sprimarykey" % n))
                column['notnull'] = utils.to_bool(
                    flask.request.form.get("column%snotnull" % n))
                schema['columns'].append(column)
            if not schema['columns']:
                raise ValueError('no columns defined')
            create_table(schema, cursor)
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create', dbid=dbid))

@blueprint.route('/<id:dbid>/<id:tableid>/schema')
def schema(dbid, tableid):
    "Display the schema for table."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(dbid)
    cursor = cnx.cursor()
    try:
        schema = get_schema(tableid, cursor)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))
    return flask.render_template('table/schema.html',
                                 db=db,
                                 schema=schema,
                                 nrows=get_nrows(tableid, cursor))

@blueprint.route('/<id:dbid>/<id:tableid>', methods=['GET', 'POST', 'DELETE'])
def rows(dbid, tableid):
    "Display rows in the table."
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        has_write_access = pleko.db.has_write_access(db)
        cnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
        try:
            schema = get_schema(tableid, cursor)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        sql = "SELECT * FROM %s" % tableid
        cursor.execute(sql)
        return flask.render_template('table/rows.html', 
                                     db=db,
                                     schema=schema,
                                     rows=list(cursor),
                                     has_write_access=has_write_access)

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        cnx = pleko.db.get_cnx(dbid)
        try:
            sql = "DROP TABLE %s" % tableid
            cnx.execute(sql)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))

@blueprint.route('/<id:dbid>/<id:tableid>/row', methods=['GET', 'POST'])
def row(dbid, tableid):
    "Add a row to the table."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(dbid)

    if utils.is_method_GET():
        try:
            schema = get_schema(tableid, cnx.cursor())
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        return flask.render_template('table/row.html', 
                                     db=db,
                                     schema=schema)
    
    elif utils.is_method_POST():
        cursor = cnx.cursor()
        try:
            schema = get_schema(tableid, cursor)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        errors = {}
        values = []
        for column in schema['columns']:
            try:
                value = flask.request.form.get(column['id'])
                if not value:
                    if column['notnull']:
                        raise ValueError('value required for')
                    else:
                        value = None
                elif column['type'] == constants.INTEGER:
                    value = int(value)
                elif column['type'] == constants.REAL:
                    value = float(value)
                values.append(value)
            except (ValueError, TypeError) as error:
                errors[column['id']] = str(error)
        if errors:
            for item in errors.items():
                flask.flash("%s: %s" % item, 'error')
            return flask.render_template('table/row.html', 
                                         db=db,
                                         schema=schema)
        try:
            with cnx:
                sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                      (tableid,
                       ','.join([c['id'] for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                cursor.execute(sql, values)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.row',
                                                dbid=dbid,
                                                tableid=tableid))
        else:
            flask.flash("%s rows in table" % get_nrows(tableid, cursor),
                        'message')
            return flask.redirect(flask.url_for('.row',
                                                dbid=dbid,
                                                tableid=tableid))

@blueprint.route('/<id:dbid>/<id:tableid>/upload', methods=['GET', 'POST'])
def upload(dbid, tableid):
    "Add CSV data to the table."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(dbid)
    cursor = cnx.cursor()
    try:
        schema = get_schema(tableid, cursor)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))

    if utils.is_method_GET():
        return flask.render_template('table/upload.html', 
                                     db=db,
                                     schema=schema)

    elif utils.is_method_POST():
        try:
            csvfile = flask.request.files['csvfile']
            lines = csvfile.read().decode('utf-8').split('\n')
            records = list(csv.reader(lines))
            header = records.pop(0)
            for n, column in enumerate(schema['columns']):
                if header[n] != column['id']:
                    raise ValueError('header/column identifier mismatch')
            # Eliminate empty records
            records = [r for r in records if r]
            try:
                for i, column in enumerate(schema['columns']):
                    type = column['type']
                    notnull = column['notnull']
                    if type == constants.INTEGER:
                        for n, record in enumerate(records):
                            value = record[i]
                            if value:
                                record[i] = int(value)
                            elif notnull:
                                raise ValueError('NULL disallowed')
                            else:
                                record[i] = None
                    elif type == constants.REAL:
                        for n, record in enumerate(records):
                            value = record[i]
                            if value:
                                record[i] = float(value)
                            elif notnull:
                                raise ValueError('NULL disallowed')
                            else:
                                record[i] = None
                    else:
                        for n, record in enumerate(records):
                            value = record[i]
                            if value:
                                record[i] = value
                            elif notnull:
                                raise ValueError('NULL disallowed')
                            else:
                                record[i] = None
            except (ValueError, TypeError, IndexError) as error:
                raise ValueError("line %s, column %s (%s): %s" %
                                 (n+1, i+1, column['id'], str(error)))
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
        return flask.redirect(flask.url_for('.rows',
                                            dbid=dbid,
                                            tableid=tableid))

@blueprint.route('/<id:dbid>/<id:tableid>/clone', methods=["GET", "POST"])
@login_required
def clone(dbid, tableid):
    "Create a clone of the table."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))

    cnx = pleko.db.get_cnx(dbid)
    cursor = cnx.cursor()
    try:
        schema = get_schema(tableid, cursor)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))

    if utils.is_method_GET():
        return flask.render_template('table/clone.html',
                                     db=db,
                                     schema=schema)

    elif utils.is_method_POST():
        try:
            schema['id'] = flask.request.form['id']
            if not constants.IDENTIFIER_RX.match(schema['id']):
                raise ValueError('invalid database identifier')
            try:
                get_schema(schema['id'], cursor)
            except ValueError:
                pass
            else:
                raise ValueError('table identifier already in use')
            create_table(schema, cursor)
            with cnx:
                colids = ','.join([c['id'] for c in schema['columns']])
                sql = "INSERT INTO %s (%s) SELECT %s FROM %s" % (schema['id'],
                                                                 colids,
                                                                 colids,
                                                                 tableid)
                cnx.execute(sql)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone',
                                                dbid=dbid,
                                                tableid=tableid))
        return flask.redirect(flask.url_for('.rows',
                                            dbid=dbid,
                                            tableid=schema['id']))
