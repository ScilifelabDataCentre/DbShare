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
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    try:
        stencil = dbshare.stencil.get_stencil(str(stencilname))
        title = f"{schema['name']} {stencil['name']}"
        context = {
            'title': flask.request.args.get('title') or title,
            'width': int(flask.request.args.get('width') or
                         flask.current_app.config['CHART_DEFAULT_WIDTH']),
            'height': int(flask.request.args.get('height') or
                         flask.current_app.config['CHART_DEFAULT_HEIGHT']),
            'url': utils.url_for_rows(db, schema, external=True, csv=True)
        }
        query = {}
        for variable in stencil['variables']:
            colname = flask.request.args.get(variable['name'])
            if not colname: 
                raise ValueError(f"no column for variable {variable['name']}")
            for column in schema['columns']:
                if column['name'] == colname: break
            else:
                raise ValueError(f"no such column {colname}")
            query[variable['name']] = colname
        context.update(query)
        spec = jinja2.Template(stencil['template']).render(**context)
        spec = json.loads(spec)
        utils.json_validate(spec, flask.current_app.config['VEGA_LITE_SCHEMA'])
    except (ValueError, TypeError,
            jinja2.TemplateError, jsonschema.ValidationError) as error:
        utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.select', dbname=dbname, sourcename=sourcename))

    # XXX Save it, redirect to its page.

        # url = utils.url_for('.render',
        #                     dbname=db['name'],
        #                     sourcename=schema['name'],
        #                     stencilname=stencil['name'] + '.json',
        #                     _query=query)
        # return flask.render_template('chart/render.html',
        #                              title=title,
        #                              db=db,
        #                              schema=schema,
        #                              spec=spec,
        #                              json_url=url)
