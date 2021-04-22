"JSON schema API endpoints."

import flask
import flask_cors

import dbshare.schema.db
import dbshare.schema.dbs
import dbshare.schema.root
import dbshare.schema.rows
import dbshare.schema.table
import dbshare.schema.view
import dbshare.schema.query
import dbshare.schema.chart
import dbshare.schema.user
import dbshare.schema.users


blueprint = flask.Blueprint('api_schema', __name__)

flask_cors.CORS(blueprint, methods=["GET"])


def get_schemas():
    return {
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
        'table/statistics': {'href':  dbshare.schema.table.statistics['$id'],
                             'title': dbshare.schema.table.statistics['title']},
        'table/create': {'href':  dbshare.schema.table.create['$id'],
                         'title': dbshare.schema.table.create['title']},
        'table/input': {'href':  dbshare.schema.table.input['$id'],
                        'title': dbshare.schema.table.input['title']},
        'view': {'href':  dbshare.schema.view.schema['$id'],
                 'title': dbshare.schema.view.schema['title']},
        'view/create': {'href':  dbshare.schema.view.create['$id'],
                        'title': dbshare.schema.view.create['title']},
        'rows': {'href':  dbshare.schema.rows.schema['$id'],
                 'title': dbshare.schema.rows.schema['title']},
        'query/input': {'href':  dbshare.schema.query.input['$id'],
                        'title': dbshare.schema.query.input['title']},
        'query/output': {'href':  dbshare.schema.query.output['$id'],
                         'title': dbshare.schema.query.output['title']},
        'chart': {'href':  dbshare.schema.chart.schema['$id'],
                  'title': dbshare.schema.chart.schema['title']},
        'chart/template': {'href':  dbshare.schema.chart.template_schema['$id'],
                           'title': dbshare.schema.chart.template_schema['title']},
        'user': {'href':  dbshare.schema.user.schema['$id'],
                 'title': dbshare.schema.user.schema['title']},
        'users': {'href':  dbshare.schema.users.schema['$id'],
                  'title': dbshare.schema.users.schema['title']},
    }

@blueprint.route('')
def schema():
    "Map of available JSON schemas."
    return flask.jsonify({
        '$id': flask.request.url,
        'title': schema.__doc__,
        'schemas': get_schemas()
    })

@blueprint.route('root')
def root():
    "JSON schema for root API."
    return flask.jsonify(dbshare.schema.root.schema)

@blueprint.route('/dbs')
def dbs():
    "JSON schema for database list API."
    return flask.jsonify(dbshare.schema.dbs.schema)

@blueprint.route('/db')
def db():
    "JSON schema for database API."
    return flask.jsonify(dbshare.schema.db.schema)

@blueprint.route('/db/edit')
def db_edit():
    "JSON schema for database edit API."
    return flask.jsonify(dbshare.schema.db.edit)

@blueprint.route('/table')
def table():
    "JSON schema for table API."
    return flask.jsonify(dbshare.schema.table.schema)

@blueprint.route('/table/statistics')
def table_statistics():
    "JSON schema for table statistics API."
    return flask.jsonify(dbshare.schema.table.statistics)

@blueprint.route('/table/create')
def table_create():
    "JSON schema for table create API."
    return flask.jsonify(dbshare.schema.table.create)

@blueprint.route('/table/input')
def table_input():
    "JSON schema for table input API."
    return flask.jsonify(dbshare.schema.table.input)

@blueprint.route('/view')
def view():
    "JSON schema for view API."
    return flask.jsonify(dbshare.schema.view.schema)

@blueprint.route('/view/create')
def view_create():
    "JSON schema for view create API."
    return flask.jsonify(dbshare.schema.view.create)

@blueprint.route('/rows')
def rows():
    "JSON schema for table/view rows API."
    return flask.jsonify(dbshare.schema.rows.schema)

@blueprint.route('/query/input')
def query_input():
    "JSON schema for query input API."
    return flask.jsonify(dbshare.schema.query.input)

@blueprint.route('/query/output')
def query_output():
    "JSON schema for query output API."
    return flask.jsonify(dbshare.schema.query.output)

@blueprint.route('/chart')
def chart():
    "JSON schema for chart API."
    return flask.jsonify(dbshare.schema.chart.schema)

@blueprint.route('/chart/template')
def chart_template():
    "JSON schema for chart template API."
    return flask.jsonify(dbshare.schema.chart.template_schema)

@blueprint.route('/user')
def user():
    "JSON schema for user API."
    return flask.jsonify(dbshare.schema.user.schema)

@blueprint.route('/users')
def users():
    "JSON schema for user list API."
    return flask.jsonify(dbshare.schema.users.schema)
