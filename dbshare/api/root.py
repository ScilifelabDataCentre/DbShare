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
    result['schema'] = {'href': constants.SCHEMA_BASE_URL}
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
    result['operations'] = {
        'database': {
            'query': {
                'title': 'Perform a query of the data in the database.',
                'href': utils.url_for_unq('api_db.query', dbname='{dbname}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    }
                },
                'method': 'POST',
                'input' : {
                    'content-type': constants.JSON_MIMETYPE,
                    'schema': {
                        'href': constants.SCHEMA_BASE_URL + '/query/input'
                    }
                },
                'output' : {
                    'content-type': constants.JSON_MIMETYPE,
                    'schema': {
                        'href': constants.SCHEMA_BASE_URL + '/query/output'
                    }
                }
            }
        }
    }
    if flask.g.current_user:
        result['operations']['database'].update({
            'create': {
                'title': 'Create a new database.',
                'href': utils.url_for_unq('api_db.database', dbname='{dbname}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    }
                },
                'method': 'PUT'
            },
            'edit': {
                'title': 'Edit the database metadata.',
                'href': utils.url_for_unq('api_db.database', dbname='{dbname}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    }
                },
                'method': 'POST',
                'input' : {
                    'content-type': constants.JSON_MIMETYPE,
                    'schema': {
                        'href': constants.SCHEMA_BASE_URL + '/db/edit'
                    }
                }
            },
            'delete': {
                'title': 'Delete the database.',
                'href': utils.url_for_unq('api_db.database', dbname='{dbname}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    }
                },
                'method': 'DELETE'
            },
            'readonly': {
                'title': 'Set the database to read-only.',
                'href': utils.url_for_unq('api_db.database', dbname='{dbname}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    }
                },
                'method': 'POST'
            },
            'readwrite': {
                'title': 'Set the database to read-write.',
                'href': utils.url_for_unq('api_db.database', dbname='{dbname}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    }
                },
                'method': 'POST'
            }
        })
        result['operations']['table'] = {
            'create': {
                'title': 'Create a new table in the database.',
                'href': utils.url_for_unq('api_table.table', dbname='{dbname}', tablename='{tablename}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    },
                    'tablename': {'title': 'Name of the table.',
                                  'type': 'string'
                    }
                },
                'method': 'PUT',
                'input' : {
                    'content-type': constants.JSON_MIMETYPE,
                    'schema': {
                        'href': constants.SCHEMA_BASE_URL + '/table/create'
                    }
                }
            },
            'delete': {
                'title': 'Delete the table from the database.',
                'href': utils.url_for_unq('api_table.table', dbname='{dbname}', tablename='{tablename}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    },
                    'tablename': {'title': 'Name of the table.',
                                  'type': 'string'
                    }
                },
                'method': 'DELETE'
            },
            'insert': {
                'title': 'Insert rows from JSON or CSV data into the table.',
                'href': utils.url_for_unq('api_table.insert', dbname='{dbname}', tablename='{tablename}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    },
                    'tablename': {'title': 'Name of the table.',
                                  'type': 'string'
                    }
                },
                'method': 'POST',
                'input' : [
                    {'content-type': constants.JSON_MIMETYPE,
                     'schema': {
                         'href': constants.SCHEMA_BASE_URL + '/table/input'
                     }
                    },
                    {'content-type': constants.CSV_MIMETYPE}
                ]
            },
            'update': {
                'title': 'Update rows in the table from CSV data.',
                'href': utils.url_for_unq('api_table.insert', dbname='{dbname}', tablename='{tablename}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    },
                    'tablename': {'title': 'Name of the table.',
                                  'type': 'string'
                    }
                },
                'method': 'POST',
                'input' : {'content-type': constants.CSV_MIMETYPE}
            },
            'empty': {
                'title': 'Empty the table; remove all rows.',
                'href': utils.url_for_unq('api_table.empty', dbname='{dbname}', tablename='{tablename}'),
                'variables': {
                    'dbname': {'title': 'Name of the database.',
                               'type': 'string'
                    },
                    'tablename': {'title': 'Name of the table.',
                                  'type': 'string'
                    }
                },
                'method': 'POST'
            }
        }
    return utils.jsonify(utils.get_json(**result), schema='/root')

