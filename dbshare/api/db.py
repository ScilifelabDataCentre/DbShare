"Database API endpoints."

import http.client
import io
import sqlite3

import flask
import flask_cors

import dbshare.db
import dbshare.query
import dbshare.api.table
import dbshare.api.user
import dbshare.api.view
from dbshare import constants
from dbshare import utils

blueprint = flask.Blueprint("api_db", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("/<name:dbname>", methods=["GET", "PUT", "POST", "DELETE"])
def database(dbname):
    """GET: List the database tables, views and metadata.
    PUT: Create the database, load any input data (Sqlite3 file, XLSX file).
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
        data = {
            "name": db["name"],
            "title": db.get("title"),
            "description": db.get("description"),
            "owner": dbshare.api.user.get_json(db["owner"]),
            "public": db["public"],
            "readonly": db["readonly"],
            "size": db["size"],
            "modified": db["modified"],
            "created": db["created"],
            "hashes": db["hashes"],
            "tables": [
                dbshare.api.table.get_json(db, table, title=True)
                for table in db["tables"].values()
            ],
            "views": [
                dbshare.api.view.get_json(db, view, title=True)
                for view in db["views"].values()
            ],
            "actions": {
                "query": {
                    "title": "Query the database.",
                    "href": utils.url_for("api_db.query", dbname=db["name"]),
                    "method": "POST",
                    "input": {
                        "content-type": constants.JSON_MIMETYPE,
                    },
                    "output": {
                        "content-type": constants.JSON_MIMETYPE,
                    },
                },
            }
        }
        if dbshare.db.has_write_access(db):
            data["actions"]["edit"] = \
                {
                    "title": "Edit the database metadata.",
                    "href": flask.request.url,
                    "method": "POST",
                    "input": {
                        "content-type": constants.JSON_MIMETYPE,
                    },
                }
            data["actions"]["create_table"] = \
                {
                    "title": "Create a new table in the database.",
                    "href": utils.url_for_unq(
                        "api_table.table", dbname=db["name"], tablename="{tablename}"
                ),
                "variables": {
                    "tablename": {"title": "Name of the table."},
                },
                "method": "PUT",
                "input": {
                    "content-type": constants.JSON_MIMETYPE,
                }
            }
            data["actions"]["create_view"] = \
                {
                    "title": "Create a new view in the database.",
                    "href": utils.url_for_unq(
                        "api_view.view", dbname=db["name"], viewname="{viewname}"
                        ),
                        "variables": {
                            "viewname": {"title": "Name of the view."},
                        },
                        "method": "PUT",
                        "input": {
                            "content-type": constants.JSON_MIMETYPE,
                        },
                }
        if dbshare.db.has_write_access(db, check_mode=False):
            if db.get("readonly"):
                data["actions"]["readwrite"] = \
                    {
                        "title": "Set the database to read-only.",
                        "href": utils.url_for("api_db.readonly", dbname=db["name"]),
                        "method": "POST",
                    }
            else:
                data["actions"]["readonly"] = \
                    {
                        "title": "Set the database to read-write.",
                        "href": utils.url_for("api_db.readwrite", dbname=db["name"]),
                        "method": "POST",
                    }
        if dbshare.db.has_write_access(db):
            data["actions"]["delete"] = \
                {
                    "title": "Delete the database.",
                    "href": flask.request.url,
                    "method": "DELETE",
                }
        return flask.jsonify(utils.get_json(**data))

    elif utils.http_PUT():
        db = dbshare.db.get_db(dbname)
        if db is not None:
            utils.abort_json(http.client.FORBIDDEN, "database exists")
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
                db = add_func(
                    dbname,
                    io.BytesIO(flask.request.get_data()),
                    flask.request.content_length,
                )
            else:
                with dbshare.db.DbSaver() as saver:
                    dbname = saver.set_name(dbname)
                    saver.initialize()
                db = saver.db
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(flask.url_for(".database", dbname=dbname))

    elif utils.http_POST(csrf=False):
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            data = flask.request.get_json()
            with dbshare.db.DbSaver(db) as saver:
                try:
                    dbname = saver.set_name(data["name"])
                except KeyError:
                    pass
                try:
                    saver.set_title(data["title"])
                except KeyError:
                    pass
                try:
                    saver.set_description(data["description"])
                except KeyError:
                    pass
                try:
                    saver.set_public(data["public"])
                except KeyError:
                    pass
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(flask.url_for(".database", dbname=dbname))

    elif utils.http_DELETE(csrf=False):
        try:
            dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        dbshare.db.delete_database(dbname)
        return ("", http.client.NO_CONTENT)


@blueprint.route("/<name:dbname>/query", methods=["POST"])
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
    except sqlite3.Error as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    except SystemError:
        flask.abort(http.client.REQUEST_TIMEOUT)
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    result = {
        "query": query,
        "sql": sql,
        "nrows": len(rows),
        "columns": columns,
        "cpu_time": timer(),
        "data": [dict(zip(columns, row)) for row in rows],
    }
    return flask.jsonify(utils.get_json(**result))


@blueprint.route("/<name:dbname>/readonly", methods=["POST"])
def readonly(dbname):
    "POST: Set the database to read-only."
    try:
        db = dbshare.db.get_check_write(dbname, check_mode=False)
        if not db["readonly"]:
            with dbshare.db.DbSaver(db) as saver:
                saver.set_readonly(True)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.redirect(flask.url_for(".database", dbname=dbname))


@blueprint.route("/<name:dbname>/readwrite", methods=["POST"])
def readwrite(dbname):
    "POST: Set the database to read-write."
    try:
        db = dbshare.db.get_check_write(dbname, check_mode=False)
        if db["readonly"]:
            with dbshare.db.DbSaver(db) as saver:
                saver.set_readonly(False)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.redirect(flask.url_for(".database", dbname=dbname))
