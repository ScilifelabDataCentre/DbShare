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
    "Available JSON schemas."
    data = {
        '$id': constants.SCHEMA_BASE_URL.rstrip('/'),
        'title': 'Available schemas.',
        'schemas': {
            'root': constants.SCHEMA_BASE_URL + 'root',
            'dbs': constants.SCHEMA_BASE_URL + 'dbs',
            'db': constants.SCHEMA_BASE_URL + 'db',
            'table': constants.SCHEMA_BASE_URL + 'table',
            'table_create': constants.SCHEMA_BASE_URL + 'table/create',
            'view': constants.SCHEMA_BASE_URL + 'view',
            'rows': constants.SCHEMA_BASE_URL + 'rows',
            'query': constants.SCHEMA_BASE_URL + 'query',
            'user': constants.SCHEMA_BASE_URL + 'user',
            'visualization': constants.SCHEMA_BASE_URL + 'visualization',
        }
    }
    return flask.jsonify(data)

@blueprint.route('/root')
def root():
    "JSON schema for the API root."
    return flask.jsonify(dbshare.schema.root.schema)

@blueprint.route('/dbs')
def dbs():
    "JSON schema for the API for db list."
    return flask.jsonify(dbshare.schema.dbs.schema)

@blueprint.route('/db')
def db():
    "JSON schema for the API for db."
    return flask.jsonify(dbshare.schema.db.schema)

@blueprint.route('/table')
def table():
    "JSON schema for the API for table."
    return flask.jsonify(dbshare.schema.table.schema)

@blueprint.route('/table/create')
def table_create():
    "JSON schema for the data for the API for creating a table."
    return flask.jsonify(dbshare.schema.table.create_schema)

@blueprint.route('/view')
def view():
    "JSON schema for the API for view."
    return flask.jsonify(dbshare.schema.view.schema)

@blueprint.route('/rows')
def rows():
    "JSON schema for the API for rows."
    return flask.jsonify(dbshare.schema.rows.schema)

@blueprint.route('/query')
def query():
    "JSON schema for the API for query."
    return flask.jsonify(dbshare.schema.query.schema)

@blueprint.route('/user')
def user():
    "JSON schema for API for user."
    return flask.jsonify(dbshare.schema.user.schema)

@blueprint.route('/visualization')
def visualization():
    "JSON schema for API for visualization."
    return flask.jsonify(dbshare.schema.visualization.schema)
