"Root API endpoint."

import flask
import flask_cors

import dbshare
import dbshare.api.user
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint("api", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("")
def root():
    "API root resource; links to other API resources."
    schema_base_url = flask.current_app.config["SCHEMA_BASE_URL"]
    result = {
        "title": "DbShare API",
        "version": dbshare.__version__,
        "databases": {"public": {"href": utils.url_for("api_dbs.public")}},
    }
    if flask.g.current_user:
        result["databases"]["owner"] = {
            "href": utils.url_for(
                "api_dbs.owner", username=flask.g.current_user["username"]
            )
        }
    result["schema"] = {"href": schema_base_url}
    if flask.g.is_admin:
        result["databases"]["all"] = {"href": utils.url_for("api_dbs.all")}
        result["users"] = {"all": {"href": utils.url_for("api_users.all")}}
    if flask.g.current_user:
        result["user"] = dbshare.api.user.get_json(flask.g.current_user["username"])
    result["operations"] = {
        "database": {
            "query": {
                "title": "Perform a database query.",
                "href": utils.url_for_unq("api_db.query", dbname="{dbname}"),
                "variables": {"dbname": {"title": "Name of the database."}},
                "method": "POST",
                "input": {
                    "content-type": constants.JSON_MIMETYPE,
                    "schema": {"href": schema_base_url + "/query/input"},
                },
                "output": {
                    "content-type": constants.JSON_MIMETYPE,
                    "schema": {"href": schema_base_url + "/query/output"},
                },
            }
        }
    }
    if flask.g.current_user:
        result["operations"]["database"].update(
            {
                "create": {
                    "title": "Create a new database.",
                    "href": utils.url_for_unq("api_db.database", dbname="{dbname}"),
                    "variables": {"dbname": {"title": "Name of the database."}},
                    "method": "PUT",
                },
                "edit": {
                    "title": "Edit the database metadata.",
                    "href": utils.url_for_unq("api_db.database", dbname="{dbname}"),
                    "variables": {"dbname": {"title": "Name of the database."}},
                    "method": "POST",
                    "input": {
                        "content-type": constants.JSON_MIMETYPE,
                        "schema": {"href": schema_base_url + "/db/edit"},
                    },
                },
                "delete": {
                    "title": "Delete the database.",
                    "href": utils.url_for_unq("api_db.database", dbname="{dbname}"),
                    "variables": {"dbname": {"title": "Name of the database."}},
                    "method": "DELETE",
                },
                "readonly": {
                    "title": "Set the database to read-only.",
                    "href": utils.url_for_unq("api_db.database", dbname="{dbname}"),
                    "variables": {"dbname": {"title": "Name of the database."}},
                    "method": "POST",
                },
                "readwrite": {
                    "title": "Set the database to read-write.",
                    "href": utils.url_for_unq("api_db.database", dbname="{dbname}"),
                    "variables": {"dbname": {"title": "Name of the database."}},
                    "method": "POST",
                },
            }
        )
        result["operations"]["table"] = {
            "create": {
                "title": "Create a new table in the database.",
                "href": utils.url_for_unq(
                    "api_table.table", dbname="{dbname}", tablename="{tablename}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "tablename": {"title": "Name of the table."},
                },
                "method": "PUT",
                "input": {
                    "content-type": constants.JSON_MIMETYPE,
                    "schema": {"href": schema_base_url + "/table/create"},
                },
            },
            "delete": {
                "title": "Delete the table from the database.",
                "href": utils.url_for_unq(
                    "api_table.table", dbname="{dbname}", tablename="{tablename}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "tablename": {"title": "Name of the table."},
                },
                "method": "DELETE",
            },
            "insert": {
                "title": "Insert rows from JSON or CSV data into the table.",
                "href": utils.url_for_unq(
                    "api_table.insert", dbname="{dbname}", tablename="{tablename}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "tablename": {"title": "Name of the table."},
                },
                "method": "POST",
                "input": [
                    {
                        "content-type": constants.JSON_MIMETYPE,
                        "schema": {"href": schema_base_url + "/table/input"},
                    },
                    {"content-type": constants.CSV_MIMETYPE},
                ],
            },
            "update": {
                "title": "Update rows in the table from CSV data.",
                "href": utils.url_for_unq(
                    "api_table.update", dbname="{dbname}", tablename="{tablename}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "tablename": {"title": "Name of the table."},
                },
                "method": "POST",
                "input": {"content-type": constants.CSV_MIMETYPE},
            },
            "empty": {
                "title": "Empty the table; remove all rows.",
                "href": utils.url_for_unq(
                    "api_table.empty", dbname="{dbname}", tablename="{tablename}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "tablename": {"title": "Name of the table."},
                },
                "method": "POST",
            },
        }
        result["operations"]["view"] = {
            "create": {
                "title": "Create a new view in the database.",
                "href": utils.url_for_unq(
                    "api_view.view", dbname="{dbname}", viewname="{viewname}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "viewname": {"title": "Name of the view."},
                },
                "method": "PUT",
                "input": {
                    "content-type": constants.JSON_MIMETYPE,
                    "schema": {"href": schema_base_url + "/view/create"},
                },
            },
            "delete": {
                "title": "Delete the view from the database.",
                "href": utils.url_for_unq(
                    "api_view.view", dbname="{dbname}", viewname="{viewname}"
                ),
                "variables": {
                    "dbname": {"title": "Name of the database."},
                    "viewname": {"title": "Name of the view."},
                },
                "method": "DELETE",
            },
        }
    return utils.jsonify(utils.get_json(**result), "/root")
