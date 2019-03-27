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
    "Query the database."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    query = get_query_from_request()
    cnx = pleko.db.get_cnx(dbname)
    for table in db['tables'].values():
        table['nrows'] = pleko.db.get_nrows(table['name'], cnx)
    return flask.render_template('query/home.html', db=db, query=query)

@blueprint.route('/<name:dbname>/rows', methods=['POST'])
def rows(dbname):
    "Display results of a query to the database."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
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


# Utility functions

def get_query_from_request(check=False):
    """Get the query data from the current request values (=form or args) data.
    Raise KeyError if a required part is missing.
    """
    result = {}
    result['select'] = flask.request.values.get('select') or ''
    if check and not result['select']:
        raise KeyError('no SELECT part')
    result['columns'] = [c.strip() for c in result['select'].split(',')]
    result['from']= flask.request.values.get('from')
    if check and not result['from']: 
        raise KeyError('no FROM part')
    result['where'] = flask.request.values.get('where') or ''
    result['orderby'] = flask.request.values.get('orderby') or ''
    result['limit'] = flask.request.values.get('limit') or ''
    try:
        result['limit'] = flask.request.values['limit']
        if result['limit'].lower() == 'none':
            result['limit'] = ''
    except KeyError:
        result['limit']= flask.current_app.config['QUERY_DEFAULT_LIMIT']
    return result

def get_sql_query(statement):
    "Create the SQL SELECT statement from its parts."
    parts = ["SELECT {select} FROM {from}".format(**statement)]
    if statement['where']:
        parts.append('WHERE ' + statement['where'])
    if statement['orderby']:
        parts.append('ORDER BY ' + statement['orderby'])
    if statement['limit']:
        parts.append('LIMIT ' + statement['limit'])
    return ' '.join(parts)
