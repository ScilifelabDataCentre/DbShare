"View API endpoints."

import http.client

import flask
import flask_cors

import dbshare.db
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint("api_view", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("/<name:dbname>/<name:viewname>", methods=["GET", "PUT", "DELETE"])
def view(dbname, viewname):
    """GET: Return the SQL schema for the view in JSON format.
    PUT: Create the view from an SQL schema in JSON format.
    DELETE: Delete the view.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname, nrows=[viewname])
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            schema = db["views"][viewname]
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        result = get_json(db, schema, complete=True)
        result.update(schema)
        result.pop("type", None)
        return flask.jsonify(utils.get_json(**result))

    elif utils.http_PUT():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbSaver(db) as saver:
                saver.add_view(flask.request.get_json(), create=True)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(
            flask.url_for("api_view.view", dbname=dbname, viewname=viewname)
        )

    elif utils.http_DELETE():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbSaver(db) as saver:
                saver.delete_view(viewname)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return ("", http.client.NO_CONTENT)


@blueprint.route("/<name:dbname>/<name:viewname>.csv")
def rows_csv(dbname, viewname):
    "Return the rows in CSV format."
    try:
        db = dbshare.db.get_check_read(dbname, nrows=[viewname])
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["views"][viewname]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        dbcnx = dbshare.db.get_cnx(dbname)
        columns = [c["name"] for c in schema["columns"]]
        colnames = ",".join([f'"{c}"' for c in columns])
        sql = f'SELECT {colnames} FROM "{viewname}"'
        try:
            cursor = utils.execute_timeout(dbcnx, sql)
        except SystemError:
            flask.abort(http.client.REQUEST_TIMEOUT)
    except sqlite3.Error:
        flask.abort(http.client.INTERNAL_SERVER_ERROR)
    writer = utils.CsvWriter(header=columns)
    writer.write_rows(cursor)
    return flask.Response(writer.getvalue(), mimetype=constants.CSV_MIMETYPE)


@blueprint.route("/<name:dbname>/<name:viewname>.json")
def rows_json(dbname, viewname):
    "Return the rows in JSON format."
    try:
        db = dbshare.db.get_check_read(dbname, nrows=[viewname])
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["views"][viewname]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        dbcnx = dbshare.db.get_cnx(dbname)
        columns = [c["name"] for c in schema["columns"]]
        colnames = ",".join([f'"{c}"' for c in columns])
        sql = f'SELECT {colnames} FROM "{viewname}"'
        try:
            cursor = utils.execute_timeout(dbcnx, sql)
        except SystemError:
            flask.abort(http.client.REQUEST_TIMEOUT)
    except sqlite3.Error:
        flask.abort(http.client.INTERNAL_SERVER_ERROR)
    result = {
        "name": viewname,
        "title": schema.get("title") or "View {}".format(viewname),
        "source": {
            "type": "view",
            "href": utils.url_for(
                "api_view.view", dbname=db["name"], viewname=viewname
            ),
        },
        "nrows": schema["nrows"],
        "data": [dict(zip(columns, row)) for row in cursor],
    }
    return flask.jsonify(utils.get_json(**result))


def get_json(db, view, complete=False, title=False):
    "Return the JSON for the view."
    result = {"name": view["name"]}
    if complete or title:
        result["description"] = view.get("description")
        result["title"] = view.get("title")
    result["nrows"] = view.get("nrows")
    result["rows"] = {
        "href": utils.url_for(
            "api_view.rows_json", dbname=db["name"], viewname=view["name"]
        )
    }
    result["data"] = {
        "href": utils.url_for(
            "api_view.rows_csv", dbname=db["name"], viewname=view["name"]
        ),
        "content-type": constants.CSV_MIMETYPE,
        "format": "csv",
    }
    if complete:
        result["database"] = {
            "href": utils.url_for("api_db.database", dbname=db["name"])
        }
        if dbshare.db.has_write_access(db):
            result["actions"] = {
                "delete": {
                    "title": "Delete the view from the database.",
                    "href": flask.request.url,
                    "method": "DELETE",
                }
            }
    else:
        result["href"] = utils.url_for(
            "api_view.view", dbname=db["name"], viewname=view["name"]
        )
    return result
