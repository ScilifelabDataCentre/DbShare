"Vega-Lite visualization create endpoints."

import copy
import json
import sqlite3

import flask
import jsonschema

import pleko.db
import pleko.user
from pleko import constants
from pleko import utils


# Rely on ordered dict items.
INITIAL = {'$schema': 'https://vega.github.io/schema/vega-lite/v3.json'}
INITIAL['title'] = 'A basic scatterplot visualization.'
INITIAL['description'] = 'A skeleton for a scatterplot.'
INITIAL['width'] = 400
INITIAL['height'] = 400
INITIAL['data'] = {'url': None, 'format': {'type': 'csv'}}
INITIAL['mark'] = 'point'
INITIAL['encoding'] = {'x': {'field': 'REPLACE', 'type': 'quantitative'},
                       'y': {'field': 'REPLACE', 'type': 'quantitative'},
                       'color': {'field': 'REPLACE', 'type': 'nominal'},
                       'shape': {'field': 'REPLACE', 'type': 'nominal'}}


blueprint = flask.Blueprint('vega-lite', __name__)

@blueprint.route('/<name:dbname>/<name:sourcename>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, sourcename):
    "Create a Vega-Lite visualization from scratch for the given table or view."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = pleko.db.get_schema(db, sourcename)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        spec = flask.request.args.get('spec')
        if not spec:
            spec = copy.deepcopy(INITIAL)
            if schema['type'] == constants.TABLE:
                url =  utils.get_url('table.rows',
                                     values=dict(dbname=db['name'],
                                                 tablename=schema['name']))
            else:
                url =  utils.get_url('view.rows', 
                                     values=dict(dbname=db['name'],
                                                 viewname=schema['name']))
            spec['data']['url'] = url + '.csv'
            spec = json.dumps(spec, indent=2)
        return flask.render_template('vega-lite/create.html',
                                     db=db,
                                     schema=schema,
                                     name=flask.request.args.get('name'),
                                     spec=spec)

    elif utils.is_method_POST():
        visualname = flask.request.form.get('name')
        strspec = flask.request.form.get('spec')
        try:
            if not visualname:
                raise ValueError('no visual name given')
            if not constants.NAME_RX.match(visualname):
                raise ValueError('invalid visual name')
            visualname = visualname.lower()
            try:
                pleko.db.get_visual(db, visualname)
            except ValueError:
                pass
            else:
                raise ValueError('visualization name already in use')
            spec = json.loads(strspec)
            jsonschema.validate(
                instance=spec,
                schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
            with pleko.db.DbContext(db) as ctx:
                ctx.add_visual(visualname, schema['name'], spec)
        except (ValueError, TypeError,
                sqlite3.Error, jsonschema.ValidationError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create',
                                                dbname=dbname,
                                                sourcename=sourcename,
                                                name=visualname,
                                                spec=strspec))
        return flask.redirect(flask.url_for('visual.display',
                                            dbname=dbname,
                                            visualname=visualname))
