"Pleko table schema web end-points."

import copy
import json
import os.path
import sqlite3

import flask

import pleko.db
from pleko import utils
from pleko.user import login_required


blueprint = flask.Blueprint('schema', __name__)

@blueprint.route('/<id:dbid>/<id:tableid>')
@login_required
def table(dbid, tableid):
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cursor = pleko.db.get_cnx(dbid).cursor()
    sql = 'PRAGMA table_info("%s")' % tableid
    cursor.execute(sql)
    rows = list(cursor)
    if len(rows) == 0:
        flask.flash('no such table in database', 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))
    schema = {'tableid': tableid,
              'columns': [{'columnid': row[1],
                           'type': row[2],
                           'notnull': bool(row[3]),
                           'defaultvalue': row[4],
                           'primarykey': bool(row[5])}
                          for row in rows]}
    return flask.render_template('schema/table.html',
                                 db=db,
                                 schema=schema)
