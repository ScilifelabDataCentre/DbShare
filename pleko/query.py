"Pleko query endpoint."

import sqlite3

import flask

import pleko.db
import pleko.table
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('query', __name__)

@blueprint.route('/<name:dbname>')
def home(dbname):
    "Create a query for the database."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    has_write_access = pleko.db.has_write_access(db)
    query = get_query_from_request(check=False)
    if query.get('select'):
        sql = None
    else:
        sql = flask.request.args.get('sql')
        if sql: sql = sql.strip()
    cnx = pleko.db.get_cnx(dbname)
    for table in db['tables'].values():
        table['nrows'] = pleko.db.get_nrows(table['name'], cnx)
    return flask.render_template('query/home.html',
                                 db=db,
                                 query=query,
                                 sql=sql,
                                 has_write_access=has_write_access)

@blueprint.route('/<name:dbname>/rows', methods=['POST'])
def rows(dbname):
    "Display results of a query to the database."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    query = {}
    try:
        query = get_query_from_request(check=True)
        cnx = pleko.db.get_cnx(dbname)
        cursor = cnx.cursor()
        sql = get_sql_query(query)
        cursor.execute(sql)
        rows = list(cursor)
        if query['columns'][0] == '*':
            try:
                columns = ["column%i" % (i+1) for i in range(len(rows[0]))]
            except IndexError:
                columns = ['columns']
        else:
            columns = query['columns']
    except (KeyError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(utils.get_absolute_url('.home',
                                                     values={'dbname': dbname},
                                                     query=query))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 query=query,
                                 columns=columns,
                                 sql=sql,
                                 rows=rows,
                                 nrows=len(rows))

@blueprint.route('/<name:dbname>/sql', methods=['POST'])
def sql(dbname):
    """Execute a complete SQL statement for the database.
    The set of allowed SQL commands excludes the clearly damaging ones.
    """
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    sql = flask.request.form.get('sql')
    try:
        if not sql:
            raise ValueError('no SQL statement provided')
        command = sql.split()[0].upper()
        cnx = pleko.db.get_cnx(dbname)
        cursor = cnx.cursor()
        cursor.execute(sql)
        rows = list(cursor)
        # Will raise IndexError if no rows returned.
        columns = ["column%i" % (i+1) for i in range(len(rows[0]))]
    except IndexError:
        flask.flash('no result returned', 'message')
        return flask.redirect(utils.get_absolute_url('.home',
                                                     values={'dbname': dbname},
                                                     query={}))
    except (ValueError, sqlite3.Error, sqlite3.Warning) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(utils.get_absolute_url('.home',
                                                     values={'dbname': dbname},
                                                     query={'sql': sql or ''}))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 query={},
                                 columns=columns,
                                 sql=sql,
                                 rows=rows,
                                 nrows=len(rows))
        

# Utility functions

def get_query_from_request(check=False):
    """Get the query data from the current request values (=form or args) data.
    Raise KeyError if a required part is missing.
    """
    result = {}
    result['select'] = flask.request.values.get('select')
    if not result['select']:
        if check:
            raise KeyError('no SELECT part')
    columns = []
    if result['select']:
        for name in result['select'].split(','):
            name = name.strip()
            try:
                pos = name.upper().index(' AS ')
                name = name[pos+len(' AS '):]
            except ValueError:
                pass
            columns.append(name)
    result['columns'] = columns
    result['from']= flask.request.values.get('from')
    if check and not result['from']: 
        raise KeyError('no FROM part')
    result['where'] = flask.request.values.get('where')
    result['orderby'] = flask.request.values.get('orderby')
    result['limit'] = flask.request.values.get('limit')
    try:
        result['limit'] = flask.request.values['limit']
    except KeyError:
        result['limit']= flask.current_app.config['QUERY_DEFAULT_LIMIT']
    else:
        if result['limit'].lower() == 'none':
            result['limit'] = None
    return result

def get_sql_query(statement):
    "Create the SQL SELECT statement from its parts."
    parts = ["SELECT {select} FROM {from}".format(**statement)]
    if statement.get('where'):
        parts.append('WHERE ' + statement['where'])
    if statement.get('orderby'):
        parts.append('ORDER BY ' + statement['orderby'])
    if statement.get('limit'):
        parts.append('LIMIT ' + statement['limit'])
    return ' '.join(parts)
