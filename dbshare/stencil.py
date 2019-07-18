"Stencil HTML endpoints."

import copy

import flask

from . import constants
from . import utils


# Hard-wired stencils.
STENCILS = [
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

def get_stencils():
    "Return the available stencils."
    return copy.deepcopy(STENCILS)

def get_stencil(stencilname):
    """Return the stencil for the given name.
    Raise ValueError if not found.
    """
    for stencil in STENCILS:
        if stencil['name'] == str(stencilname):
            return copy.deepcopy(stencil)
    else:
        raise ValueError('no such stencil')
