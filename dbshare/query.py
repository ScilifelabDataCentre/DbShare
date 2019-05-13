"Query HTMl endpoint."

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
        sql = get_sql_query(query)
        limit = flask.current_app.config['MAX_NROWS_DISPLAY']
        sql = get_sql_query(query)
        query_limited = query.copy()
        if query['limit'] is None or query['limit'] > limit:
            query_limited['limit'] = limit
        dbcnx = dbshare.db.get_cnx(dbname)
        rows = utils.execute_timeout(dbcnx, get_sql_query(query_limited))
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
                                 sql=sql,
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
    Raise KeyError if a required part is missing.
    """
    result = {}
    result['select'] = flask.request.values.get('select')
    if not result['select']:
        if check:
            raise KeyError('no SELECT part')
    # Column name must use the "AS" part if any
    result['columns'] = []
    if result['select']:
        for name in result['select'].split(','):
            result['columns'].append(utils.name_after_as(name))
    result['from']= flask.request.values.get('from')
    if check and not result['from']: 
        raise KeyError('no FROM part')
    result['where'] = flask.request.values.get('where') or None
    result['orderby'] = flask.request.values.get('orderby') or None
    try:
        limit = flask.request.values['limit']
        limit = limit.strip()
        if limit:
            result['limit'] = max(1, int(limit))
        else:
            result['limit'] = None
    except (KeyError, ValueError, TypeError):
        result['limit'] = flask.current_app.config['QUERY_DEFAULT_LIMIT']
    try:
        offset = flask.request.values['offset']
        offset = offset.strip()
        if offset:
            result['offset'] = max(1, int(offset))
        else:
            result['offset'] = None
    except (KeyError, ValueError, TypeError):
        pass
    return result

def get_sql_query(statement):
    "Create the SQL SELECT statement from its parts."
    parts = ["SELECT {select} FROM {from}".format(**statement)]
    if statement.get('where'):
        parts.append('WHERE ' + statement['where'])
    if statement.get('orderby'):
        parts.append('ORDER BY ' + statement['orderby'])
    if statement.get('limit'):
        parts.append("LIMIT %s" % statement['limit'])
        if statement.get('offset'):
            parts.append("OFFSET %s" % statement['offset'])
    return ' '.join(parts)
