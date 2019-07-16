"Chart HTML endpoints."

import flask

import dbshare.db

from . import constants
from . import utils


CHARTS = {}

blueprint = flask.Blueprint('chart', __name__)

@blueprint.route('/select/<name:dbname>/<name:tablename>')
def select(dbname, tablename):
    "Show selection of possible charts for the given table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][str(tablename)]
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    raise NotImplementedError

@blueprint.route('/show/<name:dbname>/<name:tablename>/<name:chartname>')
def show(dbname, tablename, chartname):
    "Show the given chart for the given table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][str(tablename)]
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    raise NotImplementedError
