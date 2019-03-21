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
    return flask.render_template('query/index.html',
                                 db=db,
                                 tables=pleko.db.get_tables(dbid, schema=True))

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
        part = flask.request.form['select']
        if not part: raise KeyError('no SELECT part')
        parts = {'select': part}
        part = flask.request.form['from']
        if not part: raise KeyError('no FROM part')
        parts['from'] = part
        where = flask.request.form['where'] or None
        sql = "SELECT {select} FROM {from}".format(**parts)
        if where:
            sql += ' WHERE' + where
        print(sql)
        cnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
        cursor.execute(sql)
        rows = list(cursor)
    except (KeyError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.index', dbid=dbid))
    return flask.render_template('query/rows.html',
                                 db=db,
                                 sql=sql,
                                 rows=rows)
