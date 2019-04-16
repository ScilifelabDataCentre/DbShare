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
        db = pleko.db.get_check_read(dbname, nrows=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    has_write_access = pleko.db.has_write_access(db)
    query = get_query_from_request(check=False)
    cnx = pleko.db.get_cnx(dbname)
    return flask.render_template('query/home.html',
                                 db=db,
                                 query=query,
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
        limit = flask.current_app.config['MAX_NROWS_DISPLAY']
        if query['limit'] is None or query['limit'] > limit:
            query['limit'] = limit
            flask.flash('NOTE: The number of rows displayed' +
                        f' is limited to {limit}.',
                        'message')
        cursor = pleko.db.get_cnx(dbname).cursor()
        sql = get_sql_query(query)
        cursor.execute(get_sql_query(query))
        rows = list(cursor)
        if query['columns'][0] == '*':
            try:
                columns = [f"column{i+1}" for i in range(len(rows[0]))]
            except IndexError:
                columns = ['columns']
        else:
            columns = query['columns']
    except (KeyError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname, **query))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 query=query,
                                 columns=columns,
                                 sql=sql,
                                 rows=rows)

@blueprint.route('/<name:dbname>/table', methods=['GET', 'POST'])
@pleko.user.login_required
def table(dbname):
    "Create a table containing the results of the query."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
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
            with pleko.db.DbContext(db) as ctx:
                ctx.add_table(schema, query=query)
        except (KeyError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.home',
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
    result['where'] = flask.request.values.get('where')
    result['orderby'] = flask.request.values.get('orderby')
    try:
        limit = flask.request.values['limit']
        limit = limit.strip()
        if limit:
            result['limit'] = max(1, int(limit))
        else:
            result['limit'] = None
    except (KeyError, ValueError, TypeError):
        result['limit'] = flask.current_app.config['QUERY_DEFAULT_LIMIT']
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
    return ' '.join(parts)
