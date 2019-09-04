"Stencil HTML endpoints."

import copy
import http.client
import json

import flask
import jinja2
import jsonschema

import dbshare.db
import dbshare.stencil

from . import constants
from . import utils


blueprint = flask.Blueprint('stencil', __name__)

@blueprint.route('/<name:dbname>/<name:sourcename>')
def select(dbname, sourcename):
    "Display selection of stencils to make a chart for the given table/view."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = dbshare.db.get_schema(db, sourcename)
    except KeyError:
        utils.flash_error('no such table or view')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    stencils = get_stencils()
    for stencil in stencils:
        stencil['combinations'] = combinations(stencil['variables'], schema)
    stencils = [c for c in stencils if c['combinations']]
    return flask.render_template('stencil/select.html',
                                 db=db,
                                 schema=schema,
                                 stencils=stencils)

def combinations(variables, schema, current=None):
    "Return all combinations of variables in stencil to table/view columns."
    result = []
    if current is None:
        current = []
    pos = len(current)
    annotations = schema.get('annotations', {})
    for column in schema['columns']:
        if annotations.get(column['name'], {}).get('ignore'): continue
        if isinstance(variables[pos]['type'], str):
            if column['type'] != variables[pos]['type']: continue
        elif isinstance(variables[pos]['type'], list):
            if column['type'] not in variables[pos]['type']: continue
        else:
            continue
        # XXX check annotation in variable
        if column['name'] in current: continue
        if pos + 1 == len(variables):
            result.append(dict(zip([v['name'] for v in variables],
                                   current + [column['name']])))
        else:
            result.extend(combinations(variables,
                                       schema,
                                       current+[column['name']]))
    return result

@blueprint.route('/<name:dbname>/<name:sourcename>/<nameext:stencilname>')
def render(dbname, sourcename, stencilname):
    "Render the chart for the given table/view and stencil."
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
        spec, context = get_chart_spec_context(db, schema, str(stencilname))
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.select', dbname=dbname, sourcename=sourcename))

    if stencilname.ext == 'json' or utils.accept_json():
        return utils.jsonify(spec)

    elif stencilname.ext in (None, 'html'):
        json_url = utils.url_for('.render',
                                 dbname=db['name'],
                                 sourcename=schema['name'],
                                 stencilname=str(stencilname) + '.json',
                                 _query=context)
        return flask.render_template('stencil/render.html',
                                     title=context['title'],
                                     db=db,
                                     has_write_access=dbshare.db.has_write_access(db),
                                     schema=schema,
                                     stencilname=str(stencilname),
                                     spec=spec,
                                     context=context,
                                     json_url=json_url)

    else:
        flask.abort(http.client.NOT_ACCEPTABLE)


def get_chart_spec_context(db, schema, stencilname):
    """Return the chart spec and context given the table/view schema
    and any variables given in the request.
    Raise ValueError if something is wrong.
    """
    for stencil in dbshare.stencil.get_stencils():
        if stencil['name'] == str(stencilname):
            break
    else:
        raise ValueError('no such stencil')
    try:
        context = {
            'url': utils.url_for_rows(db, schema, external=True, csv=True),
            'title': flask.request.values.get('title') or
                     f"{schema['type'].capitalize()} {schema['name']}: {stencil['name']}",
            'width': int(flask.request.values.get('width') or
                         flask.current_app.config['CHART_DEFAULT_WIDTH']),
            'height': int(flask.request.values.get('height') or
                         flask.current_app.config['CHART_DEFAULT_HEIGHT'])
        }
    except TypeError as error:
        raise ValueError(str(error))
    for variable in stencil['variables']:
        colname = flask.request.values.get(variable['name'])
        if not colname: 
            raise ValueError(f"no column for variable {variable['name']}")
        for column in schema['columns']:
            if column['name'] == colname: break
        else:
            raise ValueError(f"no such column {colname}")
        context[variable['name']] = colname
    try:
        spec = jinja2.Template(stencil['template']).render(**context)
        spec = json.loads(spec)
        utils.json_validate(spec, flask.current_app.config['VEGA_LITE_SCHEMA'])
    except (jinja2.TemplateError, jsonschema.ValidationError) as error:
        raise ValueError(str(error))
    return spec, context

def get_stencils():
    "Return the available stencils."
    # XXX Redesign, get stencils from files.
    return copy.deepcopy(STENCILS)

# XXX Redesign, split out into files.
STENCILS = [
    {'name': 'scatterplot',
     'title': 'Basic two-dimensional scatterplot.',
     'variables': [
         {'name': 'x',
          'title': 'Horizontal dimension',
          'type': ['REAL', 'INTEGER']
         },
         {'name': 'y',
          'title': 'Vertical dimension',
          'type': ['REAL', 'INTEGER']
         },
     ],
     'template': 
'''{
  "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
  "title": "{{ title }}",
  "width": {{ width }},
  "height": {{ height }},
  "data": {
    "url": "{{ url }}",
    "format": {"type": "csv"}
  },
  "mark": "point",
  "encoding": {
    "x": {
      "field": "{{ x }}",
      "type": "quantitative"
    },
    "y": {
      "field": "{{ y }}",
      "type": "quantitative"
    }
  }
}'''
    },
    {'name': 'scatterplot_color',
     'title': 'Two-dimensional scatterplot, points colored by class.',
     'variables': [
         {'name': 'x',
          'title': 'Horizontal dimension',
          'type': ['REAL', 'INTEGER']
         },
         {'name': 'y',
          'title': 'Vertical dimension',
          'type': ['REAL', 'INTEGER']
         },
         {'name': 'color',
          'title': 'Point color',
          'type': 'TEXT'
          }
     ],
     'template': 
'''{
  "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
  "title": "{{ title }}",
  "width": {{ width }},
  "height": {{ height }},
  "data": {
    "url": "{{ url }}",
    "format": {"type": "csv"}
  },
  "mark": "point",
  "encoding": {
    "x": {
      "field": "{{ x }}",
      "type": "quantitative"
    },
    "y": {
      "field": "{{ y }}",
      "type": "quantitative"
    },
    "color": {
      "field": "{{ color }}",
      "type": "nominal"
    }
  }
}'''
    },
    {'name': 'bar_graph_record_counts',
     'title': 'Bar graph of number of records per class.',
     'variables': [
         {'name': 'class',
          'title': 'Record class.',
          'type': 'TEXT'
         }
     ],
     'template':
'''{
  "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
  "title": "{{ title }}",
  "width": {{ width }},
  "height": {{ height }},
  "data": {
    "url": "{{ url }}",
    "format": {"type": "csv"}
  },
  "transform": [
    {
      "aggregate": [{
        "op": "count",
         "field": "{{ class }}", 
         "as": "counts"}],
      "groupby": ["{{ class }}"]
    }
  ],
  "mark": "bar",
  "encoding": {
    "x": {
      "field": "{{ class }}",
      "type": "nominal"
    },
    "y": {
      "field": "counts", 
      "type": "quantitative"
    }
  }
}'''
     }
]
