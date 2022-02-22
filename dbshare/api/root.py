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
    return utils.jsonify(utils.get_json(**result), "/root")
