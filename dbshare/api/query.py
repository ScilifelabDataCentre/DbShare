"Query API endpoints."

import http.client
import sqlite3

import flask
import jsonschema

import dbshare.db
import dbshare.query
from dbshare import utils


blueprint = flask.Blueprint('api_query', __name__)

@blueprint.route('/<name:dbname>')
def query(dbname):
    "Perform a query of the database; return rows."
    try:
        db = dbshare.db.get_check_read(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    timer = utils.Timer()
    try:
        query = flask.request.get_json()
        sql = dbshare.query.get_sql_statement(query)
        dbcnx = dbshare.db.get_cnx(dbname)
        cursor = utils.execute_timeout(dbcnx, sql)
    except (jsonschema.ValidationError, sqlite3.Error) as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    except SystemError:
        flask.abort(http.client.REQUEST_TIMEOUT)
    columns = [d[0] for d in cursor.description]
    query['columns'] = columns
    rows = cursor.fetchall()
    return flask.jsonify(utils.get_api(
        query=query,
        sql=sql,
        nrows=len(rows),
        cpu_time=timer(),
        data=[dict(zip(columns, row)) for row in rows]))
