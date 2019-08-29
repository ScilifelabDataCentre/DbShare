"Chart HTML endpoints."

import http.client
import json

import flask
import jinja2
import jsonschema

import dbshare.db
import dbshare.stencil

from . import constants
from . import utils


blueprint = flask.Blueprint('chart', __name__)

@blueprint.route('/<name:dbname>/<name:sourcename>/save/<name:stencilname>')
def save(dbname, sourcename, stencilname):
    "Save the chart for the given table/view and stencil."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    try:
        spec, context = get_chart_spec_context(db, schema, stencilname)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.select', dbname=dbname, sourcename=sourcename))
