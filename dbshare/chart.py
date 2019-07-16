"Chart HTML endpoints."

import flask

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
  "title": "{{ TITLE }}",
  "width": 400,
  "height": 400,
  "data": {
    "url": "{{ DATA_URL }}",
    "format": {
      "type": "csv"
    }
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
{% if color is defined %}
    ,"color": {
      "field": "{{ color }}",
      "type": "nominal"
    }
{% endif %}
{% if shape is defined %}
    ,"shape": {
      "field": "{{ shape }}",
      "type": "nominal"
    }
{% endif %}
  }
}'''
    }
]


blueprint = flask.Blueprint('chart', __name__)

@blueprint.route('/select/<name:dbname>/<name:tablename>')
def select(dbname, tablename):
    "Show selection of possible charts for the given table."
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
    charts = []
    return flask.render_template('chart/select.html',
                                 db=db,
                                 schema=schema,
                                 charts=charts)

def combine_variables_columns(chart, schema, combination=None):
    "Return all combinations of variables in chart to columns in table."
    if combination in None:
        combination = []
    raise NotImplementedError
    variable = chart['variables'][len(combination)]
    if len(combination) == len(chart['variables']): return combination
    

@blueprint.route('/show/<name:dbname>/<name:tablename>/<name:chartname>')
def show(dbname, tablename, chartname):
    "Show the given chart for the given table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][str(tablename)]
    except KeyError:
        utils.flash_error('no such table')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    raise NotImplementedError
