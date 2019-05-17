"Query HTML endpoints."

import sqlite3

import flask

import dbshare.db
import dbshare.table
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint('query', __name__)

@blueprint.route('/<name:dbname>')
def define(dbname):
    "Define a query of the database."
    try:
        db = dbshare.db.get_check_read(dbname, nrows=True)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    has_write_access = dbshare.db.has_write_access(db)
    query = get_query_from_request(check=False)
    cnx = dbshare.db.get_cnx(dbname)
    return flask.render_template('query/define.html',
                                 db=db,
                                 query=query,
                                 has_write_access=has_write_access)

@blueprint.route('/<name:dbname>/rows', methods=['POST'])
def rows(dbname):
    "Display results of a query to the database."
    utils.check_csrf_token()
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    query = {}
    try:
        query = get_query_from_request(check=True)
        query_limited = query.copy()
        limit = flask.current_app.config['MAX_NROWS_DISPLAY']
        if query['limit'] is None or query['limit'] > limit:
            query_limited['limit'] = limit
        dbcnx = dbshare.db.get_cnx(dbname)
        rows = utils.execute_timeout(dbcnx, get_sql_statement(query_limited))
        if len(rows) >= query_limited['limit']:
            utils.flash_message_limit(limit)
        if query['columns'][0] == '*':
            try:
                columns = [f"column{i+1}" for i in range(len(rows[0]))]
            except IndexError:
                columns = ['columns']
        else:
            columns = query['columns']
    except (KeyError, SystemError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.define', dbname=dbname, **query))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 query=query,
                                 columns=columns,
                                 sql=get_sql_statement(query),
                                 rows=rows)

@blueprint.route('/<name:dbname>/table', methods=['GET', 'POST'])
@dbshare.user.login_required
def table(dbname):
    "Create a table containing the results of the query."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        query = get_query_from_request(check=False)
        return flask.render_template('query/table.html',
                                     db=db,
                                     query=query)

    elif utils.http_POST():
        try:
            query = get_query_from_request(check=True)
            schema = {'name': flask.request.form.get('name')}
            with dbshare.db.DbContext(db) as ctx:
                ctx.add_table(schema, query=query)
        except (KeyError, SystemError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.define',
                                                dbname=dbname,
                                                **query))
        return flask.redirect(
            flask.url_for('table.rows', dbname=dbname,tablename=schema['name']))


def get_query_from_request(check=False):
    """Get the query data from the current request values (=form or args) data.
    Raise KeyError if a required part is missing if 'check' is True.
    """
    result = {}
    result['select'] = flask.request.values.get('select')
    if check and not result['select']:
        raise KeyError('lacking SELECT part')
    # Get result column names considering quotes and AS part, if any.
    if result['select']:
        result['columns'] = get_select_columns(result['select'])
    else:
        result['columns'] = []
    result['from']= flask.request.values.get('from')
    if check and not result['from']: 
        raise KeyError('lacking FROM part')
    result['where'] = flask.request.values.get('where') or None
    result['orderby'] = flask.request.values.get('orderby') or None
    try:
        limit = flask.request.values['limit']
        limit = limit.strip()
        if limit:
            result['limit'] = max(1, int(limit))
        else:                   # Empty string
            result['limit'] = None
    except (KeyError, ValueError, TypeError):
        result['limit'] = flask.current_app.config['QUERY_DEFAULT_LIMIT']
    try:
        offset = flask.request.values['offset']
        offset = offset.strip()
        if offset:
            result['offset'] = max(1, int(offset))
        else:                   # Empty string
            result['offset'] = None
    except (KeyError, ValueError, TypeError):
        pass
    return result

def get_select_columns(select):
    """Parse out column names from the SELECT part of the query.
    Consider quotes and AS.
    """
    result = []
    parts = []
    for token in utils.lexer(select):
        if token['value'] == ',':
            result.append(''.join(parts))
            parts = []
        elif token['type'] == 'RESERVED' and token['value'] == 'AS':
            parts = []
        elif token['type'] == 'WHITESPACE':
            pass
        else:
            parts.append(token['value'])
    if parts:
        result.append(''.join(parts))
    return result

def get_from_sources(from_):
    """Parse out table/view names from the FROM part of the query.
    Consider quotes and AS (ignored, contrary to columns)."""
    result = []
    parts = []
    before_as = True
    for token in utils.lexer(from_):
        if token['value'] == ',':
            if parts:
                result.append(''.join(parts))
                parts = []
            before_as = True
        elif token['type'] == 'RESERVED' and token['value'] == 'AS':
            if parts:
                result.append(''.join(parts))
                parts = []
            before_as = False
        elif token['type'] == 'WHITESPACE':
            pass
        elif before_as:
            parts.append(token['value'])
    if parts:
        result.append(''.join(parts))
    return result

def get_sql_statement(query):
    "Create the SQL SELECT statement from the query parts."
    parts = ["SELECT {select} FROM {from}".format(**query)]
    if query.get('where'):
        parts.append('WHERE ' + query['where'])
    if query.get('orderby'):
        parts.append('ORDER BY ' + query['orderby'])
    if query.get('limit'):
        parts.append("LIMIT %s" % query['limit'])
        if query.get('offset'):
            parts.append("OFFSET %s" % query['offset'])
    return ' '.join(parts)
