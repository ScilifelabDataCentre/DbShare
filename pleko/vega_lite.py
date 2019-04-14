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


INITIAL = {'$schema': None,     # To be set on template creation.
           'title': '{{ title }}',
           'description': '{{ description }}',
           'width': 400,
           'height': 400,
           'data': {'url': '{{ data_url }}', 'format': {'type': 'csv'}}}


blueprint = flask.Blueprint('vega-lite', __name__)

@blueprint.route('/<name:dbname>/<name:sourcename>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, sourcename):
    "Create a Vega-Lite visualization from scratch for the given table or view."
    try:
        db = pleko.db.get_check_write(dbname, nrows=[sourcename])
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
            spec['$schema'] = flask.current_app.config['VEGA_LITE_SCHEMA_URL']
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
