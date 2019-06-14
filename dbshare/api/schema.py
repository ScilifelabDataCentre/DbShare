"JSON schema API endpoints."

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

schemas = {
    'root': {'href':  dbshare.schema.root.schema['$id'],
             'title': dbshare.schema.root.schema['title']},
    'dbs': {'href':  dbshare.schema.dbs.schema['$id'],
            'title': dbshare.schema.dbs.schema['title']},
    'db': {'href':  dbshare.schema.db.schema['$id'],
           'title': dbshare.schema.db.schema['title']},
    'db/edit': {'href':  dbshare.schema.db.edit['$id'],
                'title': dbshare.schema.db.edit['title']},
    'table': {'href':  dbshare.schema.table.schema['$id'],
              'title': dbshare.schema.table.schema['title']},
    'table/create': {'href':  dbshare.schema.table.create['$id'],
                     'title': dbshare.schema.table.create['title']},
    'table/input': {'href':  dbshare.schema.table.input['$id'],
                    'title': dbshare.schema.table.input['title']},
    'view': {'href':  dbshare.schema.view.schema['$id'],
             'title': dbshare.schema.view.schema['title']},
    'rows': {'href':  dbshare.schema.rows.schema['$id'],
             'title': dbshare.schema.rows.schema['title']},
    'query/input': {'href':  dbshare.schema.query.input['$id'],
                    'title': dbshare.schema.query.input['title']},
    'query/output': {'href':  dbshare.schema.query.output['$id'],
                     'title': dbshare.schema.query.output['title']},
    'user': {'href':  dbshare.schema.user.schema['$id'],
             'title': dbshare.schema.user.schema['title']},
}


blueprint = flask.Blueprint('api_schema', __name__)

@blueprint.route('')
def schema():
    "Map of available JSON schemas."
    return flask.jsonify({
        '$id': constants.SCHEMA_BASE_URL.rstrip('/'),
        'title': schema.__doc__,
        'schemas': schemas
    })

@blueprint.route('/root')
def root():
    return flask.jsonify(dbshare.schema.root.schema)

@blueprint.route('/dbs')
def dbs():
    return flask.jsonify(dbshare.schema.dbs.schema)

@blueprint.route('/db')
def db():
    return flask.jsonify(dbshare.schema.db.schema)

@blueprint.route('/db/edit')
def db_edit():
    return flask.jsonify(dbshare.schema.db.edit)

@blueprint.route('/table')
def table():
    return flask.jsonify(dbshare.schema.table.schema)

@blueprint.route('/table/create')
def table_create():
    return flask.jsonify(dbshare.schema.table.create)

@blueprint.route('/table/input')
def table_input():
    return flask.jsonify(dbshare.schema.table.input)

@blueprint.route('/view')
def view():
    return flask.jsonify(dbshare.schema.view.schema)

@blueprint.route('/rows')
def rows():
    return flask.jsonify(dbshare.schema.rows.schema)

@blueprint.route('/query/input')
def query_input():
    return flask.jsonify(dbshare.schema.query.input)

@blueprint.route('/query/output')
def query_output():
    return flask.jsonify(dbshare.schema.query.output)

@blueprint.route('/user')
def user():
    return flask.jsonify(dbshare.schema.user.schema)
