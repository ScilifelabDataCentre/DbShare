"Table API endpoints."

import io
import http.client
import sqlite3

import flask
import flask_cors

import dbshare.db
import dbshare.table
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint("api_table", __name__)

flask_cors.CORS(blueprint, methods=["GET"])


@blueprint.route("/<name:dbname>/<name:tablename>", methods=["GET", "PUT", "DELETE"])
def table(dbname, tablename):
    """GET: Return the SQL schema for the table in JSON format.
    PUT: Create the table from an SQL schema in JSON format.
    DELETE: Delete the table.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            schema = db["tables"][tablename]
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        result = get_json(db, schema, complete=True)
        result.update(schema)
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
                schema = flask.request.get_json()
                saver.add_table(schema)
                for index in schema.get("indexes", []):
                    saver.add_index(tablename, index)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(
            flask.url_for("api_table.table", dbname=dbname, tablename=tablename)
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
                saver.delete_table(tablename)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return ("", http.client.NO_CONTENT)


@blueprint.route("/<name:dbname>/<name:tablename>.csv")
def rows_csv(dbname, tablename):
    "Return the rows in CSV format."
    try:
        db = dbshare.db.get_check_read(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        dbcnx = dbshare.db.get_cnx(dbname)
        columns = [c["name"] for c in schema["columns"]]
        colnames = ",".join([f'"{c}"' for c in columns])
        sql = f'SELECT {colnames} FROM "{tablename}"'
        try:
            cursor = utils.execute_timeout(dbcnx, sql)
        except SystemError:
            flask.abort(http.client.REQUEST_TIMEOUT)
    except sqlite3.Error:
        flask.abort(http.client.INTERNAL_SERVER_ERROR)
    writer = utils.CsvWriter(header=columns)
    writer.write_rows(cursor)
    return flask.Response(writer.getvalue(), mimetype=constants.CSV_MIMETYPE)


@blueprint.route("/<name:dbname>/<name:tablename>.json")
def rows_json(dbname, tablename):
    "Return the rows in JSON format."
    try:
        db = dbshare.db.get_check_read(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        dbcnx = dbshare.db.get_cnx(dbname)
        columns = [c["name"] for c in schema["columns"]]
        colnames = ",".join([f'"{c}"' for c in columns])
        sql = f'SELECT {colnames} FROM "{tablename}"'
        try:
            cursor = utils.execute_timeout(dbcnx, sql)
        except SystemError:
            flask.abort(http.client.REQUEST_TIMEOUT)
    except sqlite3.Error:
        flask.abort(http.client.INTERNAL_SERVER_ERROR)
    result = {
        "name": tablename,
        "title": schema.get("title") or "Table {}".format(tablename),
        "source": {
            "type": "table",
            "href": utils.url_for(
                "api_table.table", dbname=db["name"], tablename=tablename
            ),
        },
        "nrows": schema["nrows"],
        "data": [dict(zip(columns, row)) for row in cursor],
    }
    return flask.jsonify(utils.get_json(**result))


@blueprint.route("/<name:dbname>/<name:tablename>/statistics", methods=["GET"])
def statistics(dbname, tablename):
    "Return the SQL schema for the table with statistics for the columns."
    try:
        db = dbshare.db.get_check_read(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    result = get_json(db, schema, complete=False)
    dbshare.table.compute_statistics(db, schema)
    result.update(schema)
    return flask.jsonify(utils.get_json(**result))


@blueprint.route("/<name:dbname>/<name:tablename>/insert", methods=["POST"])
def insert(dbname, tablename):
    "POST: Insert rows from JSON or CSV data into the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)

    try:
        # JSON input data
        if flask.request.is_json:
            data = flask.request.get_json()
            columns = schema["columns"]
            # Check validity of values in input data.
            rows = []
            for pos, item in enumerate(data["data"]):
                values = []
                for column in columns:
                    try:
                        value = item[column["name"]]
                    except KeyError:
                        if column.get("notnull"):
                            raise ValueError(
                                f"missing key '{column['name']}'" f" in item # {pos}"
                            )
                        value = None
                    else:
                        try:
                            if column["type"] == constants.INTEGER:
                                if not isinstance(value, int):
                                    raise TypeError
                            elif column["type"] == constants.REAL:
                                if not isinstance(value, (int, float)):
                                    raise TypeError
                            elif column["type"] == constants.TEXT:
                                if not isinstance(value, str):
                                    raise TypeError
                            elif column["type"] == constants.BLOB:
                                raise TypeError
                        except TypeError:
                            raise ValueError(
                                f"'{column['name']}'invalid type" f" in item # {pos}"
                            )
                    values.append(value)
                rows.append(values)

        # CSV input data
        elif flask.request.content_type == constants.CSV_MIMETYPE:
            csvfile = io.BytesIO(flask.request.data)
            rows = dbshare.table.get_csv_rows(schema, csvfile, ",", True)

        # Unrecognized input data type
        else:
            flask.abort(http.client.UNSUPPORTED_MEDIA_TYPE)

        dbshare.table.insert_rows(db, schema, rows)
    except (ValueError, sqlite3.Error) as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for("api_table.table", dbname=dbname, tablename=tablename)
    )


@blueprint.route("/<name:dbname>/<name:tablename>/update", methods=["POST"])
def update(dbname, tablename):
    "POST: Update table rows from CSV data (JSON not implemented)."
    try:
        db = dbshare.db.get_check_write(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)

    try:
        # CSV input data
        if flask.request.content_type == constants.CSV_MIMETYPE:
            csvfile = io.BytesIO(flask.request.data)
            dbshare.table.update_csv_rows(db, schema, csvfile, ",")

        # Unrecognized input data type
        else:
            flask.abort(http.client.UNSUPPORTED_MEDIA_TYPE)
    except (ValueError, sqlite3.Error) as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for("api_table.table", dbname=dbname, tablename=tablename)
    )


@blueprint.route("/<name:dbname>/<name:tablename>/empty", methods=["POST"])
def empty(dbname, tablename):
    "Empty the table; delete all rows."
    try:
        db = dbshare.db.get_check_write(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        with dbshare.db.DbSaver(db) as saver:
            saver.empty_table(schema)
    except sqlite3.Error as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for("api_table.table", dbname=dbname, tablename=tablename)
    )


def get_json(db, table, complete=False, title=False):
    "Return JSON for the table."
    result = {"name": table["name"]}
    if complete or title:
        result["description"] = table.get("description")
        result["title"] = table.get("title")
    result["nrows"] = table["nrows"]
    result["rows"] = {
        "href": utils.url_for(
            "api_table.rows_json", dbname=db["name"], tablename=table["name"]
        )
    }
    result["data"] = {
        "href": utils.url_for(
            "api_table.rows_csv", dbname=db["name"], tablename=table["name"]
        ),
        "content-type": constants.CSV_MIMETYPE,
        "format": "csv",
    }
    if complete:
        result["database"] = {
            "href": utils.url_for("api_db.database", dbname=db["name"])
        }
        result["statistics"] = {
            "href": utils.url_for(
                "api_table.statistics", dbname=db["name"], tablename=table["name"]
            )
        }
        result["indexes"] = [
            i for i in db["indexes"].values() if i["table"] == table["name"]
        ]
        for i in result["indexes"]:
            i.pop("table")
        result["actions"] = [
            {
                "title": "Insert additional rows from JSON or CSV data into the table.",
                "href": utils.url_for_unq(
                    "api_table.insert", dbname=db["name"], tablename=table["name"]
                ),
                "method": "POST",
                "input": [
                    {"content-type": constants.JSON_MIMETYPE},
                    {"content-type": constants.CSV_MIMETYPE},
                ],
            },
            {
                "title": "Update rows in the table from CSV data according to primary key.",
                "href": utils.url_for_unq(
                    "api_table.update", dbname=db["name"], tablename=table["name"]
                ),
                "method": "POST",
                "input": {"content-type": constants.CSV_MIMETYPE},
            },
            {
                "title": "Empty the table; remove all rows.",
                "href": utils.url_for_unq(
                    "api_table.empty", dbname=db["name"], tablename=table["name"]
                ),
                "method": "POST",
            },
            {
                "title": "Delete the table from the database.",
                "href": utils.url_for_unq(
                    "api_table.table", dbname=db["name"], tablename=table["name"]
                ),
                "method": "DELETE",
            },
        ]
    else:
        result["href"] = utils.url_for(
            "api_table.table", dbname=db["name"], tablename=table["name"]
        )
    return result
