"Database lists API endpoints."

import flask

import dbportal.dbs
import dbportal.user

import dbportal.api_db

from dbportal import utils


blueprint = flask.Blueprint('api_dbs', __name__)

@blueprint.route('/public')
def public():
    "Return the list of public databases."
    dbs = dbportal.dbs.get_dbs(public=True)
    result = utils.get_api(title='Public databases',
                           databases=get_api(dbs),
                           display={'href': utils.url_for('dbs.public'),
                                    'format': 'html'})
    return flask.jsonify(result)

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Return the list of all databases."
    dbs = dbportal.dbs.get_dbs()
    result = utils.get_api(title='All databases',
                           total_size=sum([db['size'] for db in dbs]),
                           databases=get_api(dbs),
                           display={'href': utils.url_for('dbs.all'),
                                    'format': 'html'})
    return flask.jsonify(result)

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Return the list of databases owned by the given user."
    if not dbportal.dbs.has_access(username):
        return flask.abort(401)
    dbs = dbportal.dbs.get_dbs(owner=username)
    result = utils.get_api(title=f"Databases owned by {username}",
                           user={'username': username,
                                 'href': utils.url_for('api_user.api_profile',
                                                       username=username)},
                           total_size=sum([db['size'] for db in dbs]),
                           databases=get_api(dbs),
                           display={'href': utils.url_for('dbs.owner',
                                                          username=username),
                                    'format': 'html'})
    return flask.jsonify(result)

def get_api(dbs):
    "Return API JSON for the databases."
    result = {}
    for db in dbs:
        data = dbportal.api_db.get_api(db)
        data['href'] = utils.url_for('api_db.database', dbname=db['name'])
        result[db['name']] = data
    return result
