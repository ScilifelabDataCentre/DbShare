"JSON Schema API endpoints."

import flask

import dbshare.schema.root
import dbshare.schema.dbs


blueprint = flask.Blueprint('api_schema', __name__)

@blueprint.route('/')
def schema():
    return flask.redirect(flask.url_for('.root'))

@blueprint.route('/root.json')
def root():
    schema = dbshare.schema.root.schema
    schema['$id'] = flask.request.url
    schema['$schema'] = flask.current_app.config['JSONSCHEMA_URL']
    return flask.jsonify(**schema)


@blueprint.route('/dbs.json')
def dbs():
    schema = dbshare.schema.dbs.schema
    schema['$id'] = flask.request.url
    schema['$schema'] = flask.current_app.config['JSONSCHEMA_URL']
    return flask.jsonify(**schema)
