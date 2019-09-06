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

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
def save(dbname):
    "Save the chart in the database given the table/view and stencil."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        sourcename = flask.request.values['sourcename']
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    try:
        stencilname = flask.request.values['stencilname']
    except KeyError:
        utils.flash_error('no such stencil')
        return flask.redirect(flask.url_for('stencil.select',
                                            dbname=dbname,
                                            sourcename=sourcename))
    try:
        spec, context = dbshare.stencil.get_chart_spec_context(db,
                                                               schema, 
                                                               stencilname)
    except (KeyError, ValueError) as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for('stencil.select',
                                            dbname=dbname,
                                            sourcename=sourcename))

    if utils.http_GET():
        return flask.render_template('chart/save.html',
                                     db=db,
                                     schema=schema,
                                     stencilname=stencilname,
                                     context=context)

    elif utils.http_POST():
        try:
            with dbshare.db.DbContext(db) as ctx:
                chartname = flask.request.form['name']
                ctx.add_chart(chartname, schema, spec)
        except (ValueError, jsonschema.ValidationError) as error:
            utils.flash_error(str(error))
            return flask.redirect(flask.url_for('stencil.select',
                                                dbname=dbname,
                                                sourcename=sourcename))
        return flask.redirect(
            flask.url_for('.display', dbname=dbname, chartname=chartname))

@blueprint.route('/<name:dbname>/<nameext:chartname>')
def display(dbname, chartname):
    "Display the database chart."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        chart = db['charts'][str(chartname)]
    except KeyError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('db.display', dbname=db['name']))
    try:
        schema = dbshare.db.get_schema(db, chart['schema'])
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if chartname.ext == 'json' or utils.accept_json():
        return flask.jsonify(chart['spec'])

    elif chartname.ext in (None, 'html'):
        url = flask.url_for('.display', dbname=dbname, chartname=chartname)
        return flask.render_template('chart/display.html',
                                     db=db,
                                     schema=schema,
                                     chart=chart,
                                     has_write_access=dbshare.db.has_write_access(db),
                                     json_url=url + '.json')

@blueprint.route('/<name:dbname>/<name:chartname>/edit',
                 methods=['GET', 'POST', 'DELETE'])
def edit(dbname, chartname):
    "Edit the named chart. Or delete it."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(
            flask.url_for('.display', dbname=dbname, chartname=chartname))
    try:
        chart = db['charts'][str(chartname)]
    except KeyError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('db.display', dbname=db['name']))

    if utils.http_GET():
        return flask.render_template('chart/edit.html', db=db, chart=chart)

    elif utils.http_POST():
        try:
            spec = json.loads(flask.request.form['spec'])
            with dbshare.db.DbContext(db) as ctx:
                ctx.update_chart(chartname, spec)
        except (KeyError, ValueError, jsonschema.ValidationError) as error:
            utils.flash_error(error)
        return flask.redirect(
            flask.url_for('.display', dbname=dbname, chartname=chartname))

    elif utils.http_DELETE():
        with dbshare.db.DbContext(db) as ctx:
            ctx.delete_chart(chartname)
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
