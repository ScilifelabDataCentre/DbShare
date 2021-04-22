"Database API endpoints."

import http.client
import io
import sqlite3

import flask
import flask_cors
import jsonschema

import dbshare.db
import dbshare.query
import dbshare.api.schema
import dbshare.api.table
import dbshare.api.user
import dbshare.api.view
from dbshare import constants
from dbshare import utils

blueprint = flask.Blueprint('api_db', __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route('/<name:dbname>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def database(dbname):
    """GET: List the database tables, views and metadata.
    PUT: Create the database, load the data if any input.
    POST: Edit the database metadata.
    DELETE: Delete the database.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname, nrows=True)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        return utils.jsonify(utils.get_json(**get_json(db, complete=True)),
                             '/db')
 
    elif utils.http_PUT():
        db = dbshare.db.get_db(dbname)
        if db is not None:
            utils.abort_json(http.client.FORBIDDEN, 'database exists')
        if not flask.request.content_length:
            add_func = None
        elif flask.request.content_type is None:
            add_func = None
        elif flask.request.content_type == constants.SQLITE3_MIMETYPE:
            add_func = dbshare.db.add_sqlite3_database
        elif flask.request.content_type == constants.XLSX_MIMETYPE:
            add_func = dbshare.db.add_xlsx_database
        else:
            flask.abort(http.client.UNSUPPORTED_MEDIA_TYPE)
        try:
            if add_func:
                db = add_func(dbname,
                              io.BytesIO(flask.request.get_data()),
                              flask.request.content_length)
            else:
                with dbshare.db.DbContext() as ctx:
                    dbname = ctx.set_name(dbname)
                    ctx.initialize()
                db = ctx.db
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(flask.url_for('.database', dbname=dbname))

    elif utils.http_POST(csrf=False):
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            data = flask.request.get_json()
            utils.json_validate(data, dbshare.schema.db.edit)
            with dbshare.db.DbContext(db) as ctx:
                try:
                    dbname = ctx.set_name(data['name'])
                except KeyError:
                    pass
                try:
                    ctx.set_title(data['title'])
                except KeyError:
                    pass
                try:
                    ctx.set_description(data['description'])
                except KeyError:
                    pass
                try:
                    ctx.set_public(data['public'])
                except KeyError:
                    pass
        except (jsonschema.ValidationError, ValueError) as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(flask.url_for('.database', dbname=dbname))

    elif utils.http_DELETE(csrf=False):
        try:
            dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        dbshare.db.delete_database(dbname)
        return ('', http.client.NO_CONTENT)

@blueprint.route('/<name:dbname>/query', methods=['POST'])
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
    rows = cursor.fetchall()
    result = {
        'query': query,
        'sql': sql,
        'nrows': len(rows),
        'columns': columns,
        'cpu_time': timer(),
        'data': [dict(zip(columns, row)) for row in rows]
    }
    return utils.jsonify(utils.get_json(**result), '/query/output')

@blueprint.route('/<name:dbname>/readonly', methods=['POST'])
def readonly(dbname):
    "POST: Set the database to read-only."
    try:
        db = dbshare.db.get_check_write(dbname, check_mode=False)
        if not db['readonly']:
            with dbshare.db.DbContext(db) as ctx:
                ctx.set_readonly(True)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.redirect(flask.url_for('.database', dbname=dbname))

@blueprint.route('/<name:dbname>/readwrite', methods=['POST'])
def readwrite(dbname):
    "POST: Set the database to read-write."
    try:
        db = dbshare.db.get_check_write(dbname, check_mode=False)
        if db['readonly']:
            with dbshare.db.DbContext(db) as ctx:
                ctx.set_readonly(False)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.redirect(flask.url_for('.database', dbname=dbname))

def get_json(db, complete=False):
    "Return the JSON for the database."
    result = {'name': db['name'],
              'title': db.get('title'),
              'description': db.get('description'),
              'owner': dbshare.api.user.get_json(db['owner']),
              'public': db['public'],
              'readonly': db['readonly'],
              'size': db['size'],
              'modified': db['modified'],
              'created': db['created'],
              'hashes': db['hashes']
    }
    if complete:
        result['tables'] = [dbshare.api.table.get_json(db, table, title=True)
                            for table in db['tables'].values()]
        result['views'] = [dbshare.api.view.get_json(db, view)
                           for view in db['views'].values()]
    return result
