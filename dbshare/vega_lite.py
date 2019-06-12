"Vega-Lite visualization create HTMl endpoints."

import copy
import json
import sqlite3

import flask
import jsonschema

import dbshare.db
import dbshare.user

from . import constants
from . import utils


INITIAL = {'$schema': None,     # To be set on template creation.
           'title': '{{ title }}',
           'width': None,       # To be set on template creation.
           'height': None,      # To be set on template creation.
           'data': {'url': '{{ DATA_URL }}', 'format': {'type': 'csv'}}}


blueprint = flask.Blueprint('vega-lite', __name__)

@blueprint.route('/<name:dbname>/<name:sourcename>', methods=['GET', 'POST'])
@dbshare.user.login_required
def create(dbname, sourcename):
    "Create a Vega-Lite visualization from scratch for the given table or view."
    try:
        db = dbshare.db.get_check_write(dbname, nrows=[sourcename])
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbshare.db.get_schema(db, sourcename)
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if utils.http_GET():
        spec = flask.request.args.get('spec')
        if not spec:
            spec = copy.deepcopy(INITIAL)
            config = flask.current_app.config
            spec['$schema'] = config['VEGA_LITE_SCHEMA_URL']
            spec['width']   = config['VEGA_LITE_DEFAULT_WIDTH']
            spec['height']  = config['VEGA_LITE_DEFAULT_HEIGHT']
            spec['data']['url'] = utils.url_for_rows(db=db,
                                                     schema=schema,
                                                     external=True,
                                                     csv=True)
            spec = json.dumps(spec, indent=2)
        return flask.render_template('vega-lite/create.html',
                                     db=db,
                                     schema=schema,
                                     name=flask.request.args.get('name'),
                                     spec=spec)

    elif utils.http_POST():
        visualname = flask.request.form.get('name')
        strspec = flask.request.form.get('spec')
        try:
            if not visualname:
                raise ValueError('no visual name given')
            if not constants.NAME_RX.match(visualname):
                raise ValueError('invalid visual name')
            visualname = visualname.lower()
            try:
                dbshare.db.get_visual(db, visualname)
            except ValueError:
                pass
            else:
                raise ValueError('visualization name already in use')
            spec = json.loads(strspec)
            utils.json_validate(spec,
                                flask.current_app.config['VEGA_LITE_SCHEMA'])
            with dbshare.db.DbContext(db) as ctx:
                ctx.add_visual(visualname, schema['name'], spec)
        except (ValueError, TypeError,
                sqlite3.Error, jsonschema.ValidationError) as error:
            utils.flash_error(error)
            return flask.redirect(flask.url_for('.create',
                                                dbname=dbname,
                                                sourcename=sourcename,
                                                name=visualname,
                                                spec=strspec))
        return flask.redirect(flask.url_for('visual.display',
                                            dbname=dbname,
                                            visualname=visualname))
