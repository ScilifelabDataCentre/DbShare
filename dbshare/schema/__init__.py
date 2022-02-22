"Retro-fix URLs for the current site."

import flask

from dbshare.schema import root
from dbshare.schema import db
from dbshare.schema import dbs
from dbshare.schema import rows
from dbshare.schema import table
from dbshare.schema import view
from dbshare.schema import query
from dbshare.schema import user
from dbshare.schema import users


def set_base_url(base_url):
    "Set the URL in the schemas to reflect the current server."
    flask.current_app.config["SCHEMA_BASE_URL"] = base_url
    for schema in [
        root.schema,
        db.schema,
        db.edit,
        dbs.schema,
        rows.schema,
        table.schema,
        table.statistics,
        table.create,
        table.input,
        view.schema,
        view.create,
        query.input,
        query.output,
        user.schema,
        users.schema,
    ]:
        schema["$id"] = base_url + schema["$id"]
