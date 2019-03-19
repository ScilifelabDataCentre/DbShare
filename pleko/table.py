"Pleko table endpoints."

import sqlite3

import flask

import pleko.db
import pleko.master
from pleko import constants
from pleko import utils
from pleko.user import login_required

def get_schema(cursor, tableid):
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
        tableid = flask.request.form.get('tableid')
        if not tableid:
            raise ValueError('no table identifier given')
        if not constants.IDENTIFIER_RX.match(tableid):
            raise ValueError('invalid table identifier')
        cnx = pleko.db.get_cnx(dbid)
        try:
            cursor = cnx.cursor()
            sql = "SELECT COUNT(*) FROM sqlite_master WHERE name=?"
            cursor.execute(sql, (tableid,))
            if cursor.fetchone()[0] != 0:
                raise ValueError('table identifier already defined')
            identifiers = set()
            columns = []
            for n in range(flask.current_app.config['TABLE_INITIAL_COLUMNS']):
                identifier = flask.request.form.get("column%sid" % n)
                if not identifier: break
                if not constants.IDENTIFIER_RX.match(identifier):
                    raise ValueError("invalid identifier in column %s" % (n+1))
                if identifier in identifiers:
                    raise ValueError("repeated identifier in column %s" % (n+1))
                identifiers.add(identifier)
                column = {'identifier': identifier}
                type = flask.request.form.get("column%stype" % n)
                if type not in constants.COLUMN_TYPES:
                    raise ValueError("invalid type in column %s" % (n+1))
                column['type'] = type
                column['notnull'] = utils.to_bool(
                    flask.request.form.get("column%snotnull" % n))
                columns.append(column)
            if not columns:
                raise ValueError('no columns defined')
            primarykey = flask.request.form.get('columnprimarykey')
            if primarykey:
                try:
                    primarykey = int(primarykey)
                    if primarykey < 0: raise ValueError
                    if primarykey >= len(columns): raise ValueError
                    columns[primarykey]['primarykey'] = True
                except ValueError:
                    pass
            coldefs = []
            for column in columns:
                coldef = "{identifier} {type}".format(**column)
                if column.get('primarykey'):
                    coldef += ' PRIMARY KEY'
                if column['notnull']:
                    coldef += ' NOT NULL'
                coldefs.append(coldef)
            sql = "CREATE TABLE %s (%s)" % (tableid, ', '.join(coldefs))
            cursor.execute(sql)
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        finally:
            cnx.close()

@blueprint.route('/<id:dbid>/<id:tableid>/schema')
def schema(dbid, tableid):
    "Display the schema for table."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(dbid)
    try:
        cursor = cnx.cursor()
        try:
            schema = get_schema(cursor, tableid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        sql = "SELECT COUNT(*) FROM %s" % tableid
        cursor.execute(sql)
        nrows = cursor.fetchone()[0]
        return flask.render_template('table/schema.html',
                                     db=db,
                                     schema=schema,
                                     nrows=nrows)
    finally:
        cnx.close()

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
        try:
            cursor = cnx.cursor()
            try:
                schema = get_schema(cursor, tableid)
            except ValueError as error:
                flask.flash(str(error), 'error')
                return flask.redirect(flask.url_for('db.index', dbid=dbid))
            sql = "SELECT * FROM %s" % tableid
            cursor.execute(sql)
            rows = list(cursor)
            return flask.render_template('table/rows.html', 
                                         db=db,
                                         schema=schema,
                                         rows=rows,
                                         has_write_access=has_write_access)
        finally:
            cnx.close()

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        cnx = pleko.db.get_cnx(dbid)
        try:
            cursor = cnx.cursor()
            try:
                sql = "DROP TABLE %s" % tableid
                cursor.execute(sql)
            except sqlite3.Error as error:
                flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        finally:
            cnx.close()

@blueprint.route('/<id:dbid>/<id:tableid>/row', methods=['GET', 'POST'])
def row(dbid, tableid):
    "Add a row to the table."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(dbid)
    try:
        cursor = cnx.cursor()
        try:
            schema = get_schema(cursor, tableid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))

        if utils.is_method_GET():
            return flask.render_template('table/add.html', 
                                         db=db,
                                         schema=schema)

        elif utils.is_method_POST():
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
                return flask.render_template('table/add.html', 
                                             db=db,
                                             schema=schema)
            try:
                with cnx:
                    sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                          (tableid,
                           ','.join([c['id'] for c in schema['columns']]),
                           ','.join('?' * len(values)))
                    cursor.execute(sql, values)
            except sqlite3.Error as error:
                flask.flash(str(error), 'error')
                return flask.redirect(flask.url_for('.row',
                                                    dbid=dbid,
                                                    tableid=tableid))
            else:
                return flask.redirect(flask.url_for('.rows',
                                                    dbid=dbid,
                                                    tableid=tableid))
    finally:
        cnx.close()
