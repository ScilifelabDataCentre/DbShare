"Retro-fix URLs for the current site."

import flask

from . import root
from . import db
from . import dbs
from . import rows
from . import table
from . import view
from . import query
from . import chart
from . import user
from . import users


def set_base_url(base_url):
    "Set the URL in the schemas to reflect the current server."
    flask.current_app.config['SCHEMA_BASE_URL'] = base_url
    for schema in [root.schema,
                   db.schema, db.edit,
                   dbs.schema,
                   rows.schema,
                   table.schema, table.statistics, table.create, table.input,
                   view.schema, view.create,
                   query.input, query.output,
                   chart.schema, chart.template_schema,
                   user.schema,
                   users.schema]:
        schema['$id'] = base_url + schema['$id']
        print(schema["$id"])
