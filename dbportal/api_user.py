"User profile API endpoints."

import flask

import dbportal.template
import dbportal.user

from dbportal import utils


blueprint = flask.Blueprint('api_user', __name__)

@blueprint.route('/profile/<name:username>')
@dbportal.user.login_required
def profile(username):
    "Return the API JSON profile of the given user."
    user = get_user(username=username)
    if user is None:
        abort(404)
    if not is_admin_or_self(user):
        abort(401)
    user.pop('password')
    user.pop('apikey', None)
    ndbs, total_size = dbportal.db.get_usage(username)
    user['total_size'] = total_size
    user['databases'] = {'href': utils.url_for('api_dbs.api_owner',
                                               username=user['username'])}
    user['display'] = {'href': utils.url_for('user.profile',
                                             username=user['username']),
                       'format': 'html'}
    return flask.jsonify(utils.get_api(**user))

def get_api(username):
    "Get the API JSON for a user or owner."
    return {'username': username,
            'href': utils.url_for('api_user.profile', username=username)}
