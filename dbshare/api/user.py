"User display API endpoints."

import http.client

import flask
import flask_cors

import dbshare.user
from dbshare import utils


blueprint = flask.Blueprint("api_user", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("/<name:username>")
def user(username):
    "Return the API JSON user display."
    user = dbshare.user.get_user(username=username)
    if user is None:
        flask.abort(http.client.NOT_FOUND)
    if not dbshare.user.is_admin_or_self(user):
        flask.abort(http.client.UNAUTHORIZED)
    # Remove sensitive information.
    user.pop("password")
    user.pop("apikey", None)
    user["total_size"] = dbshare.db.get_usage(username)[1]
    user["databases"] = {
        "href": utils.url_for("api_dbs.owner", username=user["username"])
    }
    return flask.jsonify(utils.get_json(**user))


def get_json(username):
    "Get the JSON for a user or owner."
    return {
        "username": username,
        "href": utils.url_for("api_user.user", username=username),
    }
