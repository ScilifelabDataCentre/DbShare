"Relational database resource (reldb). Flask blueprint."

import os.path
import sqlite3

import flask

import pleko.constants
import pleko.resource
import pleko.utils


def filepath(rid):
    return os.path.join(flask.current_app.config['RELDB_DIRPATH'], rid) + '.sqlite3'

def create(rid):
    "Create the database file."
    assert pleko.constants.IDENTIFIER_RX.match(rid)
    try:
        db = sqlite3.connect(filepath(rid))
    except sqlite3.Error as error:
        raise ValueError(str(error))
    else:
        db.close()


blueprint = flask.Blueprint('reldb', __name__)

@blueprint.route('/index/<id:rid>', methods=["GET", "POST"])
def index(rid):
    "Index for the relational database."
    try:
        resource = pleko.resource.get_resource_check_read(rid, db=flask.g.db)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    db = sqlite3.connect(filepath(resource['rid']))
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type=?", ('table',))
    tables = [{'name': r[0]} for r in cursor]
    db.close()
    return flask.render_template('reldb/index.html',
                                 resource=resource,
                                 tables=tables)
