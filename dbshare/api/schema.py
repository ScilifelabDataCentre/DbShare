"JSON Schema API endpoints."

import flask

import dbshare.schema.db
import dbshare.schema.dbs
import dbshare.schema.root
import dbshare.schema.rows
import dbshare.schema.table
import dbshare.schema.view
import dbshare.schema.user


blueprint = flask.Blueprint('api_schema', __name__)

@blueprint.route('/')
def schema():
    "Redirect to the JSON schema for the API root."
    return flask.redirect(flask.url_for('.root'))

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

@blueprint.route('/view')
def view():
    "JSON schema for the API for view."
    return flask.jsonify(dbshare.schema.view.schema)

@blueprint.route('/view')
def rows():
    "JSON schema for the API for rows."
    return flask.jsonify(dbshare.schema.rows.schema)

@blueprint.route('/user')
def user():
    "JSON schema for API for user."
    return flask.jsonify(dbshare.schema.user.schema)
