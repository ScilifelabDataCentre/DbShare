"Database lists API endpoints."

import http.client

import flask

import dbshare.dbs
import dbshare.user

import dbshare.api_db
import dbshare.api_user

from dbshare import utils


blueprint = flask.Blueprint('api_dbs', __name__)

@blueprint.route('/public')
def public():
    "Return the list of public databases."
    dbs = dbshare.dbs.get_dbs(public=True)
    result = utils.get_api(title='Public databases',
                           databases=get_api(dbs),
                           display={'href': utils.url_for('dbs.public'),
                                    'format': 'html'})
    return flask.jsonify(result)

@blueprint.route('/all')
@dbshare.user.admin_required
def all():
    "Return the list of all databases."
    dbs = dbshare.dbs.get_dbs()
    result = utils.get_api(title='All databases',
                           total_size=sum([db['size'] for db in dbs]),
                           databases=get_api(dbs),
                           display={'href': utils.url_for('dbs.all'),
                                    'format': 'html'})
    return flask.jsonify(result)

@blueprint.route('/owner/<name:username>')
@dbshare.user.login_required
def owner(username):
    "Return the list of databases owned by the given user."
    if not dbshare.dbs.has_access(username):
        return flask.abort(http.client.UNAUTHORIZED)
    dbs = dbshare.dbs.get_dbs(owner=username)
    result = utils.get_api(title=f"Databases owned by {username}",
                           user=dbshare.api_user.get_api(username),
                           total_size=sum([db['size'] for db in dbs]),
                           databases=get_api(dbs),
                           display={'href': utils.url_for('dbs.owner',
                                                          username=username),
                                    'format': 'html'})
    return flask.jsonify(result)

def get_api(dbs):
    "Return API JSON for the databases."
    result = []
    for db in dbs:
        data = dbshare.api_db.get_api(db)
        data['href'] = utils.url_for('api_db.database', dbname=db['name'])
        result.append(data)
    return result
