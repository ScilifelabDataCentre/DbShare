"Users lists API endpoints."

import http.client

import flask

import dbshare.system

from .. import utils


blueprint = flask.Blueprint('api_users', __name__)

@blueprint.route('/all')
def all():
    "Return the list of all user accounts."
    cursor = dbshare.system.get_cursor()
    sql = "SELECT username, email, role, status, created, modified" \
          " FROM users"
    cursor.execute(sql)
    users = [{'username': row[0],
              'email':    row[1],
              'role':     row[2],
              'status':   row[3],
              'created':  row[4],
              'modified': row[5],
              'href':     utils.url_for('api_user.user', username=row[0])}
             for row in cursor]
    result = {
        'title': 'All user accounts.',
        'users': users
    }
    return utils.jsonify(utils.get_json(**result))
