"Chart HTML endpoints."

import http.client
import json

import flask
import jinja2
import jsonschema

import dbshare.db

from . import constants
from . import utils


CHARTS = [
    {'name': 'scatterplot',
     'title': 'Basic two-dimensional scatterplot.',
     'variables': [
         {'name': 'x',
          'title': 'Horizontal dimension',
          'type': 'REAL'
         },
         {'name': 'y',
          'title': 'Vertical dimension',
          'type': 'REAL'
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
          'type': 'REAL'
         },
         {'name': 'y',
          'title': 'Vertical dimension',
          'type': 'REAL'
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


blueprint = flask.Blueprint('chart', __name__)

@blueprint.route('/<name:dbname>/<name:tablename>/select')
def select(dbname, tablename):
    "Display selection of possible charts for the given table."
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
    charts = CHARTS.copy()
    for chart in charts:
        chart['combinations'] = combinations(chart['variables'],
                                             schema['columns'])
    charts = [c for c in charts if c['combinations']]
    return flask.render_template('chart/select.html',
                                 db=db,
                                 schema=schema,
                                 charts=charts)

def combinations(variables, columns, current=None):
    "Return all combinations of variables in chart to columns in table."
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

@blueprint.route('/<name:dbname>/<name:tablename>/render/<nameext:chartname>')
def render(dbname, tablename, chartname):
    "Render the given chart for the given table."
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
        for chart in CHARTS:
            if chart['name'] == str(chartname): break
        else:
            raise ValueError('no such chart')
        title = f"{schema['name']} {chart['name']}"
        context = {
            'title': flask.request.args.get('title') or title,
            'width': int(flask.request.args.get('width') or
                         flask.current_app.config['CHART_DEFAULT_WIDTH']),
            'height': int(flask.request.args.get('height') or
                         flask.current_app.config['CHART_DEFAULT_HEIGHT']),
            'url': utils.url_for_rows(db, schema, external=True, csv=True)
        }
        query = {}
        for variable in chart['variables']:
            colname = flask.request.args.get(variable['name'])
            if not colname: 
                raise ValueError(f"no column for variable {variable['name']}")
            for column in schema['columns']:
                if column['name'] == colname: break
            else:
                raise ValueError(f"no such column {colname}")
            query[variable['name']] = colname
        context.update(query)
        spec = json.loads(jinja2.Template(chart['template']).render(**context))
        utils.json_validate(spec, flask.current_app.config['VEGA_LITE_SCHEMA'])
    except (ValueError, TypeError,
            jinja2.TemplateError, jsonschema.ValidationError) as error:
        utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.select', dbname=dbname, tablename=tablename))

    if chartname.ext == 'json' or utils.accept_json():
        return utils.jsonify(spec)

    elif chartname.ext in (None, 'html'):
        url = utils.url_for('.render',
                            dbname=db['name'],
                            tablename=schema['name'],
                            chartname=chart['name'] + '.json',
                            _query=query)
        return flask.render_template('chart/render.html',
                                     title=title,
                                     db=db,
                                     schema=schema,
                                     spec=spec,
                                     json_url=url)

    else:
        flask.abort(http.client.NOT_ACCEPTABLE)
