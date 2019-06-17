"User profile API endpoints."

import http.client

import flask

import dbshare.user

from .. import utils


blueprint = flask.Blueprint('api_user', __name__)

@blueprint.route('/<name:username>')
@dbshare.user.login_required
def user(username):
    "Return the API JSON user profile."
    user = dbshare.user.get_user(username=username)
    if user is None:
        flask.abort(http.client.NOT_FOUND)
    if not dbshare.user.is_admin_or_self(user):
        flask.abort(http.client.UNAUTHORIZED)
    # Remove sensitive information.
    user.pop('password')
    user.pop('apikey', None)
    user['total_size'] = dbshare.db.get_usage(username)[1]
    user['databases'] = {'href': utils.url_for('api_dbs.owner',
                                               username=user['username'])}
    user['templates'] = {'href': utils.url_for('api_templates.owner',
                                               username=user['username'])}
    return utils.jsonify(utils.get_json(**user), schema='/user')

def get_json(username):
    "Get the JSON for a user or owner."
    return {'username': username,
            'href': utils.url_for('api_user.user', username=username)}
