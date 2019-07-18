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

@blueprint.route('/<name:dbname>/<name:tablename>/select')
def select(dbname, tablename):
    "Display selection of stencils to make a chart for the given table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    stencils = dbshare.stencil.get_stencils()
    for stencil in stencils:
        stencil['combinations'] = combinations(stencil['variables'],
                                             schema['columns'])
    stencils = [c for c in stencils if c['combinations']]
    return flask.render_template('chart/select.html',
                                 db=db,
                                 schema=schema,
                                 stencils=stencils)

def combinations(variables, columns, current=None):
    "Return all combinations of variables in stencil to columns in table."
    result = []
    if current is None:
        current = []
    pos = len(current)
    for column in columns:
        if variables[pos]['type'] != column['type']: continue
        if column['name'] in current: continue
        if pos + 1 == len(variables):
            result.append(dict(zip([v['name'] for v in variables],
                                   current + [column['name']])))
        else:
            result.extend(combinations(variables,
                                       columns,
                                       current+[column['name']]))
    return result

@blueprint.route('/<name:dbname>/<name:tablename>/render/<nameext:stencilname>')
def render(dbname, tablename, stencilname):
    "Render the chart for the given table and stencil."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][str(tablename)]
        schema['type'] = constants.TABLE
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    try:
        stencil = dbshare.stencil.get_stencil(stencilname)
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
            flask.url_for('.select', dbname=dbname, tablename=tablename))

    if stencilname.ext == 'json' or utils.accept_json():
        return utils.jsonify(spec)

    elif stencilname.ext in (None, 'html'):
        url = utils.url_for('.render',
                            dbname=db['name'],
                            tablename=schema['name'],
                            stencilname=stencil['name'] + '.json',
                            _query=query)
        return flask.render_template('chart/render.html',
                                     title=title,
                                     db=db,
                                     schema=schema,
                                     spec=spec,
                                     json_url=url)

    else:
        flask.abort(http.client.NOT_ACCEPTABLE)
