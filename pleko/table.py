"Pleko table endpoints."

import csv
import sqlite3

import flask

import pleko.db
import pleko.master
from pleko import constants
from pleko import utils
from pleko.user import login_required

def get_nrows(tableid, dbcnx):
    "Get the number of rows in the table."
    cursor = dbcnx.cursor()
    cursor.execute("SELECT COUNT(*) FROM %s" % tableid)
    return cursor.fetchone()[0]


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
                column['unique'] = utils.to_bool(
                    flask.request.form.get("column%sunique" % n))
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
    try:
        schema = db['tables'][tableid]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))
    nrows = get_nrows(tableid, pleko.db.get_cnx(dbid))
    return flask.render_template('table/schema.html',
                                 db=db,
                                 schema=schema,
                                 nrows=nrows)

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
        try:
            schema = db['tables'][tableid]
        except KeyError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        cnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
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
        try:
            with pleko.db.DbContext(db) as ctx:
                ctx.delete_table(tableid)
        except (ValueError, sqlite3.Error) as error:
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

    if utils.is_method_GET():
        try:
            schema = db['tables'][tableid]
        except KeyError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        return flask.render_template('table/row.html', 
                                     db=db,
                                     schema=schema)
    
    elif utils.is_method_POST():
        try:
            schema = db['tables'][tableid]
        except KeyError as error:
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
        dbcnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
        try:
            with dbcnx:
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
            flask.flash("%s rows in table" % get_nrows(tableid,dbcnx),'message')
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
    try:
        schema = db['tables'][tableid]
    except KeyError as error:
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
            cnx = pleko.db.get_cnx(dbid)
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

    try:
        schema = db['tables'][tableid]
    except KeyError as error:
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
            if schema['id'] in db['tables']:
                raise ValueError('table identifier already in use')
            with pleko.db.DbContext(db) as ctx:
                ctx.add_table(schema)
            cnx = ctx.cnx
            cursor = cnx.cursor()
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
