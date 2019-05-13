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
    return flask.jsonify(**dbshare.schema.root.schema)


@blueprint.route('/dbs.json')
def dbs():
    return flask.jsonify(**dbshare.schema.dbs.schema)
