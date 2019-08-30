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

@blueprint.route('/<name:dbname>/<name:sourcename>/<nameext:chartname>')
def display(dbname, sourcename, chartname):
    "Display the named chart for the given table/view."
    raise NotImplementedError

@blueprint.route('/<name:dbname>/<name:sourcename>/<name:stencilname>/save',
                 methods=['GET', 'POST'])
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
        spec, context = dbshare.stencil.get_chart_spec_context(db,
                                                               schema,
                                                               stencilname)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for('stencil.select',
                                            dbname=dbname,
                                            sourcename=sourcename))

    if utils.http_GET():
        return flask.render_template('chart/save.html')

    elif utils.http_POST():
        raise NotImplementedError

@blueprint.route('/<name:dbname>/<name:sourcename>/<name:chartname>/edit',
                 methods=['GET', 'POST', 'DELETE'])
def edit(dbname, sourcename, chartname):
    "Edit the named chart for the given table/view. Or delete it."
    try:
        db = get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('.display', dbname=dbname))

