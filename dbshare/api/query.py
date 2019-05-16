"Query API endpoints."

import http.client
import sqlite3

import flask

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
    try:
        data = flask.request.get_json()
        query = {'select': data['select'],
                 'from': data['from'],
                 'where': data.get('where') or None,
                 'orderby': data.get('orderby') or None,
                 'limit': data.get('limit') or None,
                 'offset': data.get('offset') or None}
        if not query['select']: raise KeyError
        if not query['from']: raise KeyError
        query['columns'] = []
        for name in query['select'].split(','):
            query['columns'].append(utils.name_after_as(name))
        dbcnx = dbshare.db.get_cnx(dbname)
        rows = utils.execute_timeout(dbcnx, dbshare.query.get_sql_query(query))
    except (KeyError, sqlite3.Error):
        flask.abort(http.client.BAD_REQUEST)
    except SystemError:
        flask.abort(http.client.REQUEST_TIMEOUT)
    if query['columns'][0] == '*':
        try:
            columns = [f"column{i+1}" for i in range(len(rows[0]))]
        except IndexError:
            columns = ['columns']
    else:
        columns = query['columns']
    return flask.jsonify(utils.get_api(
        query=query,
        nrows=len(rows),
        data=[dict(zip(columns, row)) for row in rows]))
