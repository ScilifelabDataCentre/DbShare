"Root API endpoint."

import flask

import dbshare.api.user

from .. import constants
from .. import utils

blueprint = flask.Blueprint('api', __name__)


@blueprint.route('')
def root():
    "API root resource; links to other API resources."
    result = {'title': 'DbShare', 
              'version': flask.current_app.config['VERSION'],
              'databases': {
                  'public': {'href': utils.url_for('api_dbs.public')}
              },
              'templates': {
                  'public': {'href': utils.url_for('api_templates.public')}
              }
    }
    if flask.g.current_user:
        result['databases']['owner'] = {
            'href': utils.url_for('api_dbs.owner',
                                  username=flask.g.current_user['username'])
        }
        result['templates']['owner'] = {
            'href': utils.url_for('api_templates.owner',
                                  username=flask.g.current_user['username'])
        }
    if flask.g.is_admin:
        result['databases']['all'] = {
            'href': utils.url_for('api_dbs.all')
        }
        result['templates']['all'] = {
            'href': utils.url_for('api_templates.all')
        }
        result['users'] = {
            'all': utils.url_for('api_users.all')
        }
    if flask.g.current_user:
        result['user'] = dbshare.api.user.get_json(
            flask.g.current_user['username'])
    result['schema'] = {'href': constants.SCHEMA_BASE_URL}
    return utils.jsonify(utils.get_json(**result), schema='/root')

