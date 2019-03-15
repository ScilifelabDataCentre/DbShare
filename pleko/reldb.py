"Relational database resource (reldb). Flask blueprint."

import os.path
import sqlite3

import flask

from pleko import constants
from pleko import utils
from pleko.user import login_required
import pleko.resource


def filepath(rid):
    return os.path.join(flask.current_app.config['RELDB_DIRPATH'], rid) + '.sqlite3'

def create(rid):
    "Create the database file."
    assert constants.IDENTIFIER_RX.match(rid)
    try:
        db = sqlite3.connect(filepath(rid))
    except sqlite3.Error as error:
        raise ValueError(str(error))
    else:
        db.close()

def table_exists(reldb, tablename):
    "Does the table exist?"
    sql = "SELECT COUNT(*) FROM sqlite_master WHERE name=? AND type=?"
    cursor = reldb.cursor()
    cursor.execute(sql, (tablename, 'table'))
    return bool(cursor.fetchone()[0])

blueprint = flask.Blueprint('reldb', __name__)

@blueprint.route('/<id:rid>')
def index(rid):
    "List of the tables in the relational database."
    try:
        resource = pleko.resource.get_resource_check_read(rid, db=flask.g.db)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    reldb = sqlite3.connect(filepath(resource['rid']))
    cursor = reldb.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type=?", ('table',))
    tables = [{'name': r[0]} for r in cursor]
    for table in tables:
        sql = "SELECT COUNT(*) FROM %s" % table['name']
        cursor.execute(sql)
        table['nrows'] = cursor.fetchone()[0]
    reldb.close()
    may_create_table = pleko.resource.has_write_access(resource)
    return flask.render_template('reldb/index.html',
                                 resource=resource,
                                 tables=tables,
                                 may_create_table=may_create_table)

@blueprint.route('/<id:rid>/schema/<id:tablename>')
def schema(rid, tablename):
    "Display the schema of the table."
    try:
        resource = pleko.resource.get_resource_check_read(rid, db=flask.g.db)
        reldb = sqlite3.connect(filepath(resource['rid']))
        if not table_exists(reldb, tablename):
            raise ValueError('no such table')
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cursor = reldb.cursor()
    cursor.execute('PRAGMA table_info("%s")' % tablename)
    columns = [{'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'primarykey': row[5]}
               for row in cursor]
    reldb.close()
    has_write_access = pleko.resource.has_write_access(resource)
    return flask.render_template('reldb/table.html',
                                 resource=resource,
                                 tablename=tablename,
                                 columns=columns,
                                 has_write_access=has_write_access)

@blueprint.route('/<id:rid>/table', methods=["GET", "POST"])
@login_required
def create_table(rid):
    "Create a table."
    try:
        resource = pleko.resource.get_resource_check_write(rid, db=flask.g.db)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    if utils.is_method_GET():
        return flask.render_template('reldb/create_table.html',
                                     resource=resource)
    elif utils.is_method_POST():
        reldb = sqlite3.connect(filepath(resource['rid']))
        try:
            tablename = flask.request.form.get('tablename')
            if not tablename: raise KeyError('no tablename given')
            if not constants.IDENTIFIER_RX.match(tablename):
                raise ValueError('invalid tablename identifier')
            if table_exists(reldb, tablename):
                raise ValueError('table already exists')
            columnname = flask.request.form.get('columnname')
            if not columnname: raise KeyError('no columnname given')
            if not constants.IDENTIFIER_RX.match(columnname):
                raise ValueError('invalid columnname identifier')
            columntype = flask.request.form.get('columntype')
            if columntype not in constants.RELDB_COLUMN_TYPES:
                raise ValueError('invalid column type')
            primarykey = utils.to_bool(flask.request.form.get('primarykey'))
            notnull = utils.to_bool(flask.request.form.get('notnull'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        else:
            sql = "CREATE TABLE %s (" % tablename
            sql += "%s %s" % (columnname, columntype)
            if primarykey:
                sql += ' PRIMARY KEY'
            if notnull:
                sql += ' NOT NULL'
            sql += ')'
            with reldb:
                reldb.execute(sql)
        reldb.close()
        return flask.redirect(flask.url_for('.index', rid=resource['rid']))
        
