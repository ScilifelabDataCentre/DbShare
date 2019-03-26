"Pleko query endpoint."

import sqlite3

import flask

import pleko.db
import pleko.table
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('query', __name__)

@blueprint.route('/<id:dbid>')
def home(dbid):
    "Query the database."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    statement = {'select': flask.request.args.get('select') or '',
                 'from': flask.request.args.get('from') or '',
                 'where': flask.request.args.get('where') or '',
                 'orderby': flask.request.args.get('orderby') or ''}
    try:
        statement['limit'] = flask.request.args['limit']
        if statement['limit'].lower() == 'none':
            statement['limit'] = None
    except KeyError:
        statement['limit']= flask.current_app.config['QUERY_DEFAULT_LIMIT']
    cnx = pleko.db.get_cnx(dbid)
    for table in db['tables'].values():
        table['nrows'] = pleko.db.get_nrows(table['id'], cnx)
    return flask.render_template('query/home.html',
                                 db=db,
                                 statement=statement,
                                 tables=sorted(db['tables'].values(),
                                               key=lambda t: t['id']))

@blueprint.route('/<id:dbid>/rows', methods=['POST'])
def rows(dbid):
    "Display results of a query to the database."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        select = get_select_from_form()
        cnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
        sql = get_sql_select(select)
        cursor.execute(sql)
        rows = list(cursor)
        if select['columns'][0] == '*':
            try:
                columns = ["column%i" % (i+1) for i in range(len(rows[0]))]
            except IndexError:
                columns = ['columns']
        else:
            columns = select['columns']
    except (KeyError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(utils.get_absolute_url('.home',
                                                     values={'dbid':dbid},
                                                     query=select))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 select=select,
                                 columns=columns,
                                 sql=sql,
                                 rows=rows,
                                 nrows=len(rows))


# Utility functions

def get_select_from_form():
    """Get the select data from the current request form data.
    Raise KeyError if a required part is missing.
    """
    result = {}
    result['select'] = flask.request.form['select']
    if not result['select']:
        raise KeyError('no SELECT part')
    result['columns'] = [c.strip() for c in result['select'].split(',')]
    result['from']= flask.request.form['from']
    if not result['from']: 
        raise KeyError('no FROM part')
    result['where'] = flask.request.form['where'] or ''
    result['orderby'] = flask.request.form['orderby'] or ''
    result['limit'] = flask.request.form['limit'] or ''
    return result

def get_sql_select(statement):
    "Create the SQL SELECT statement from its parts."
    parts = ["SELECT {select} FROM {from}".format(**statement)]
    if statement['where']:
        parts.append('WHERE ' + statement['where'])
    if statement['orderby']:
        parts.append('ORDER BY ' + statement['orderby'])
    if statement['limit']:
        parts.append('LIMIT ' + statement['limit'])
    return ' '.join(parts)
