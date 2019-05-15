"JSON Schema API endpoints."

import flask

import dbshare.schema.db
import dbshare.schema.dbs
import dbshare.schema.root
import dbshare.schema.table
import dbshare.schema.view
import dbshare.schema.user


blueprint = flask.Blueprint('api_schema', __name__)

@blueprint.route('/')
def schema():
    return flask.redirect(flask.url_for('.root'))

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

@blueprint.route('/view')
def view():
    return flask.jsonify(dbshare.schema.view.schema)

@blueprint.route('/user')
def user():
    return flask.jsonify(dbshare.schema.user.schema)
