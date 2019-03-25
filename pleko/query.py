"Pleko query endpoint."

import sqlite3

import flask

import pleko.db
import pleko.table
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('query', __name__)

@blueprint.route('/<id:dbid>')
def index(dbid):
    "Query database."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    statement = {'select': flask.request.args.get('select') or '',
                 'from': flask.request.args.get('from') or '',
                 'where': flask.request.args.get('where') or ''}
    try:
        statement['limit'] = flask.request.args['limit']
        if statement['limit'].lower() == 'none':
            statement['limit'] = None
    except KeyError:
        statement['limit']= flask.current_app.config['QUERY_DEFAULT_LIMIT']
    cnx = pleko.db.get_cnx(dbid)
    cursor = cnx.cursor()
    for table in db['tables'].values():
        table['nrows'] = pleko.table.get_nrows(table['id'], cursor=cursor)
    return flask.render_template('query/index.html',
                                 db=db,
                                 statement=statement,
                                 tables=db['tables'])

@blueprint.route('/<id:dbid>/rows', methods=['POST'])
def rows(dbid):
    "Display results of a query to the database."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    try:
        statement = {}
        statement['select'] = flask.request.form['select']
        if not statement['select']: raise KeyError('no SELECT part')
        columns = [c.strip() for c in statement['select'].split(',')]
        statement['from']= flask.request.form['from']
        if not statement['from']: raise KeyError('no FROM part')
        sql = "SELECT {select} FROM {from}".format(**statement)
        statement['where'] = flask.request.form['where'] or None
        if statement['where']:
            sql += ' WHERE ' + statement['where']
        statement['limit'] = flask.request.form['limit'] or None
        if statement['limit']:
            sql += ' LIMIT ' + statement['limit']
        cnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
        cursor.execute(sql)
        rows = list(cursor)
        if columns[0] == '*':
            columns = ["column%i" % (i+1) for i in range(len(rows[0]))]
    except (KeyError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(utils.get_absolute_url('.index',
                                                     values={'dbid':dbid},
                                                     query=statement))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 statement=statement,
                                 sql=sql,
                                 columns=columns,
                                 rows=rows,
                                 nrows=len(rows))
