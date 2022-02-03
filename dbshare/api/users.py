"Users lists API endpoints."

import http.client

import flask
import flask_cors

import dbshare.system
from dbshare import utils


blueprint = flask.Blueprint("api_users", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("/all")
@utils.admin_required
def all():
    "Return the list of all user accounts."
    sql = "SELECT username, email, role, status, created, modified" " FROM users"
    users = [
        {
            "username": row[0],
            "email": row[1],
            "role": row[2],
            "status": row[3],
            "created": row[4],
            "modified": row[5],
            "href": utils.url_for("api_user.user", username=row[0]),
        }
        for row in flask.g.syscnx.execute(sql)
    ]
    result = {"title": "All user accounts.", "users": users}
    return utils.jsonify(utils.get_json(**result), "/users")
