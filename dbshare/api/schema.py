"JSON Schema API endpoints."

import flask

import dbshare.schema.db
import dbshare.schema.dbs
import dbshare.schema.root
import dbshare.schema.rows
import dbshare.schema.table
import dbshare.schema.view
import dbshare.schema.query
import dbshare.schema.user
import dbshare.schema.visualization
from dbshare import constants


blueprint = flask.Blueprint('api_schema', __name__)

@blueprint.route('')
def schema():
    "Map of available JSON schemas."
    data = {
        '$id': constants.SCHEMA_BASE_URL.rstrip('/'),
        'title': schema.__doc__,
        'schemas': {}
    }
    for key in ['root', 'dbs', 'db', 'table', 'table_spec', 'table_data',
                'view', 'rows', 'query', 'user', 'visualization']:
        data['schemas'][key] = {'href': constants.SCHEMA_BASE_URL + key}
    return flask.jsonify(data)

@blueprint.route('/root')
def root():
    return flask.jsonify(dbshare.schema.root.schema)

@blueprint.route('/dbs')
def dbs():
    return flask.jsonify(dbshare.schema.dbs.schema)

@blueprint.route('/db')
def db():
    return flask.jsonify(dbshare.schema.db.schema)

@blueprint.route('/table')
def table():
    return flask.jsonify(dbshare.schema.table.schema)

@blueprint.route('/table_spec')
def table_spec():
    return flask.jsonify(dbshare.schema.table.schema_spec)

@blueprint.route('/table_data')
def table_data():
    return flask.jsonify(dbshare.schema.table.schema_data)

@blueprint.route('/view')
def view():
    return flask.jsonify(dbshare.schema.view.schema)

@blueprint.route('/rows')
def rows():
    return flask.jsonify(dbshare.schema.rows.schema)

@blueprint.route('/query')
def query():
    return flask.jsonify(dbshare.schema.query.schema)

@blueprint.route('/user')
def user():
    return flask.jsonify(dbshare.schema.user.schema)

@blueprint.route('/visualization')
def visualization():
    return flask.jsonify(dbshare.schema.visualization.schema)
