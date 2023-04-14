"Table HTML endpoints."

import copy
import csv
import http.client
import sqlite3
import statistics as statistics_module

import flask

import dbshare.db

from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint("table", __name__)


@blueprint.route("/<name:dbname>", methods=["GET", "POST"])
@utils.login_required
def create(dbname):
    "Create a table with columns in the database."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        dbshare.db.check_quota()
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    if utils.http_GET():
        return flask.render_template("table/create.html", db=db)

    elif utils.http_POST():
        try:
            schema = {
                "name": flask.request.form.get("name"),
                "title": flask.request.form.get("title") or None,
                "description": flask.request.form.get("description") or None,
                "nrows": 0,
            }
            schema["columns"] = []
            for n in range(flask.current_app.config["TABLE_INITIAL_COLUMNS"]):
                name = flask.request.form.get(f"column{n}name")
                if not name:
                    break
                if not constants.NAME_RX.match(name):
                    raise ValueError(f"invalid name in column {n+1}")
                column = {"name": name}
                type = flask.request.form.get(f"column{n}type")
                if type not in constants.COLUMN_TYPES:
                    raise ValueError(f"invalid type in column {n+1}")
                column["type"] = type
                column["notnull"] = utils.to_bool(
                    flask.request.form.get(f"column{n}notnull")
                )
                schema["columns"].append(column)
            try:
                npk = int(flask.request.form["column_primarykey"])
            except (KeyError, ValueError, TypeError):
                pass
            else:
                try:
                    schema["columns"][npk]["primarykey"] = True
                except IndexError:
                    pass
            with dbshare.db.DbSaver(db) as saver:
                saver.add_table(schema)
        except ValueError as error:
            utils.flash_error(error)
            return flask.redirect(flask.url_for(".create", dbname=dbname))
        else:
            return flask.redirect(
                flask.url_for(".rows", dbname=dbname, tablename=schema["name"])
            )


@blueprint.route("/<name:dbname>/<name:tablename>")
def rows(dbname, tablename):
    "Display the rows in the table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        columns = [c["name"] for c in schema["columns"]]
        dbcnx = dbshare.db.get_cnx(dbname)
        colnames = ",".join([f'"{c}"' for c in columns])
        sql = f'SELECT rowid, {colnames} FROM "{tablename}"'
        limit = flask.current_app.config["MAX_NROWS_DISPLAY"]
        if schema.get("nrows", 0) > limit:
            sql += f" LIMIT {limit}"
            utils.flash_message_limit(limit)
        cursor = utils.execute_timeout(dbcnx, sql)
    except (SystemError, sqlite3.Error) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for(".schema", tablename=tablename))
    views = []
    for viewname, view in db["views"].items():
        if tablename in view["sources"]:
            views.append(viewname)
    updateable = bool([c for c in schema["columns"] if c.get("primarykey")])
    return flask.render_template(
        "table/rows.html",
        db=db,
        schema=schema,
        title=schema.get("title") or "Table {}".format(tablename),
        views=views,
        rows=cursor,
        updateable=updateable,
        has_write_access=dbshare.db.has_write_access(db),
    )


@blueprint.route(
    "/<name:dbname>/<name:tablename>/edit", methods=["GET", "POST", "DELETE"]
)
@utils.login_required
def edit(dbname, tablename):
    "Edit the table metadata. Or delete the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    if utils.http_GET():
        return flask.render_template("table/edit.html", db=db, schema=schema)

    elif utils.http_POST():
        try:
            with dbshare.db.DbSaver(db) as saver:
                schema["title"] = flask.request.form.get("title") or None
                schema["description"] = flask.request.form.get("description") or None
                saver.update_table(schema, reset_cache=False)
        except (ValueError, sqlite3.Error) as error:
            utils.flash_error(error)
        return flask.redirect(
            flask.url_for(".rows", dbname=dbname, tablename=tablename)
        )

    elif utils.http_DELETE():
        try:
            with dbshare.db.DbSaver(db) as saver:
                saver.delete_table(str(tablename))
        except (ValueError, sqlite3.Error) as error:
            utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))


@blueprint.route("/<name:dbname>/<name:tablename>/column", methods=["GET", "POST"])
@utils.login_required
def column(dbname, tablename):
    "Add a column to the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    if utils.http_GET():
        return flask.render_template("table/column_add.html", db=db, schema=schema)

    elif utils.http_POST():
        try:
            column = {
                "name": flask.request.form.get("name"),
                "type": flask.request.form.get("type"),
                "notnull": utils.to_bool(flask.request.form.get("notnull")),
            }
            with dbshare.db.DbSaver(db) as saver:
                saver.add_table_column(schema, column)
        except (ValueError, sqlite3.Error) as error:
            utils.flash_error(error)
        return flask.redirect(
            flask.url_for(".schema", dbname=dbname, tablename=tablename)
        )


@blueprint.route("/<name:dbname>/<name:tablename>/empty", methods=["POST"])
@utils.login_required
def empty(dbname, tablename):
    "Empty the table; delete all rows."
    utils.check_csrf_token()
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    try:
        with dbshare.db.DbSaver(db) as saver:
            saver.empty_table(schema)
    except sqlite3.Error as error:
        utils.flash_error(error)
    return flask.redirect(flask.url_for(".rows", dbname=dbname, tablename=tablename))


@blueprint.route("/<name:dbname>/<name:tablename>/schema")
def schema(dbname, tablename):
    "Display the schema for a table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    indexes = [i for i in db["indexes"].values() if i["table"] == tablename]
    return flask.render_template(
        "table/schema.html",
        db=db,
        schema=schema,
        indexes=indexes,
        has_write_access=dbshare.db.has_write_access(db),
    )


@blueprint.route("/<name:dbname>/<name:tablename>/index", methods=["GET", "POST"])
@utils.login_required
def index_create(dbname, tablename):
    "Create an index on the table in the database."
    try:
        db = dbshare.db.get_check_write(dbname)
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    positions = list(range(len(schema["columns"])))

    if utils.http_GET():
        dbshare.db.set_nrows(db, targets=db["tables"].keys())
        return flask.render_template(
            "table/index_create.html", db=db, schema=schema, positions=positions
        )

    elif utils.http_POST():
        try:
            index = {"unique": utils.to_bool(flask.request.form.get("unique"))}
            index["columns"] = []
            for pos in positions:
                column = flask.request.form.get("position%i" % pos)
                if column:
                    index["columns"].append(column)
                else:
                    break
            with dbshare.db.DbSaver(db) as saver:
                saver.add_index(schema["name"], index)
        except (ValueError, sqlite3.Error) as error:
            utils.flash_error(error)
            return flask.redirect(
                flask.url_for(".index_create", dbname=dbname, tablename=tablename)
            )
        else:
            return flask.redirect(
                flask.url_for(".schema", dbname=dbname, tablename=tablename)
            )


# 'indexname' is not a proper name
@blueprint.route(
    "/<name:dbname>/<name:tablename>/index/<indexname>", methods=["POST", "DELETE"]
)
@utils.login_required
def index_delete(dbname, tablename, indexname):
    "Delete the index. 'tablename' is not needed, but included for consistency."
    utils.check_csrf_token()
    try:
        db = dbshare.db.get_check_write(dbname)
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        for index in db["indexes"].values():
            if index["name"] == indexname:
                tablename = index["table"]
                break
        else:
            raise ValueError("no such index in database")
        with dbshare.db.DbSaver(db) as saver:
            saver.delete_index(indexname)
    except (ValueError, sqlite3.Error) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    return flask.redirect(flask.url_for(".schema", dbname=dbname, tablename=tablename))


@blueprint.route("/<name:dbname>/<name:tablename>/row", methods=["GET", "POST"])
@utils.login_required
def row_insert(dbname, tablename):
    "Insert a row into the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        dbshare.db.check_quota()
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        schema = db["tables"][tablename]
        print(schema)
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    if utils.http_GET():
        try:
            duplicate = int(flask.request.args["duplicate"])
            if duplicate <= 0: raise ValueError
            if duplicate > schema["nrows"]: raise ValueError
        except (KeyError, ValueError):
            row = {}
        else:
            dbcnx = dbshare.db.get_cnx(dbname)
            cursor = dbcnx.cursor()
            names = ",".join([f'''"{c['name']}"''' for c in schema["columns"]])
            sql = f"""SELECT {names} FROM "{schema['name']}" WHERE rowid=?"""
            cursor.execute(sql, (duplicate,))
            rows = cursor.fetchall()
            if len(rows) != 1:
                utils.flash_error("no such row in table")
                return flask.redirect(
                    flask.url_for(".rows", dbname=dbname, tablename=tablename)
                )
            row = rows[0]
        return flask.render_template(
            "table/row_insert.html", db=db, schema=schema, row=row
        )

    elif utils.http_POST():
        values, errors = get_row_values_errors(schema["columns"])
        if errors:
            for item in errors.items():
                utils.flash_error("%s: %s" % item)
            return flask.render_template(
                "table/row_insert.html", db=db, schema=schema, row=values
            )
        try:
            insert_rows(db, schema, [values])
        except sqlite3.Error as error:
            utils.flash_error(error)
            return flask.render_template(
                "table/row_insert.html", db=db, schema=schema, row=values
            )
        utils.flash_message("Row inserted.")
        return flask.redirect(
            flask.url_for(".row_insert", dbname=dbname, tablename=tablename)
        )


@blueprint.route(
    "/<name:dbname>/<name:tablename>/row/<int:rowid>", methods=["GET", "POST", "DELETE"]
)
@utils.login_required
def row_edit(dbname, tablename, rowid):
    "Edit or delete a row into the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    # Do not check for quota; a loop-hole, but let it slide...
    dbcnx = dbshare.db.get_cnx(dbname)
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    if utils.http_GET():
        cursor = dbcnx.cursor()
        names = ",".join([f'''"{c['name']}"''' for c in schema["columns"]])
        sql = f"""SELECT {names} FROM "{schema['name']}" WHERE rowid=?"""
        cursor.execute(sql, (rowid,))
        rows = cursor.fetchall()
        if len(rows) != 1:
            utils.flash_error("no such row in table")
            return flask.redirect(
                flask.url_for(".rows", dbname=dbname, tablename=tablename)
            )
        return flask.render_template(
            "table/row_edit.html", db=db, schema=schema, row=rows[0], rowid=rowid
        )

    elif utils.http_POST():
        values, errors = get_row_values_errors(schema["columns"])
        if errors:
            for item in errors.items():
                utils.flash_error("%s: %s" % item)
            return flask.render_template(
                "table/row_edit.html", db=db, schema=schema, row=values, rowid=rowid
            )
        try:
            with dbshare.db.DbSaver(db) as saver:
                with saver.dbcnx:
                    names = ",".join(['"%(name)s"=?' % c for c in schema["columns"]])
                    sql = f'UPDATE "{tablename}" SET {names} WHERE rowid=?'
                    values = values + (rowid,)
                    saver.dbcnx.execute(sql, values)
        except sqlite3.Error as error:
            utils.flash_error(error)
        else:
            utils.flash_message("Row updated.")
        return flask.redirect(
            flask.url_for(".rows", dbname=dbname, tablename=tablename)
        )

    elif utils.http_DELETE():
        with dbshare.db.DbSaver(db) as saver:
            with saver.dbcnx:
                sql = f"""DELETE FROM "{schema['name']}" WHERE rowid=?"""
                saver.dbcnx.execute(sql, (rowid,))
                saver.update_table(schema)
        return flask.redirect(
            flask.url_for(".rows", dbname=dbname, tablename=tablename)
        )


@blueprint.route("/<name:dbname>/<name:tablename>/insert")
@utils.login_required
def insert(dbname, tablename):
    "Insert data from a file into the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        dbshare.db.check_quota()
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    return flask.render_template("table/insert.html", db=db, schema=schema)


@blueprint.route("/<name:dbname>/<name:tablename>/insert/csv", methods=["POST"])
@utils.login_required
def insert_csv(dbname, tablename):
    "Insert data from a CSV file into the table."
    utils.check_csrf_token()
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        dbshare.db.check_quota()
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        delimiter = flask.request.form.get("delimiter") or "comma"
        try:
            delimiter = flask.current_app.config["CSV_FILE_DELIMITERS"][delimiter][
                "char"
            ]
        except KeyError:
            raise ValueError("invalid delimiter")
        csvfile = flask.request.files["csvfile"]
        header = utils.to_bool(flask.request.form.get("header"))
        rows = get_csv_rows(schema, csvfile, delimiter, header)
        insert_rows(db, schema, rows)
        utils.flash_message(f"Inserted {len(rows)} rows.")
    except (ValueError, sqlite3.Error) as error:
        utils.flash_error(error)
        return flask.redirect(
            flask.url_for(".insert", dbname=dbname, tablename=tablename)
        )
    return flask.redirect(flask.url_for(".rows", dbname=dbname, tablename=tablename))


@blueprint.route("/<name:dbname>/<name:tablename>/update")
@utils.login_required
def update(dbname, tablename):
    "Update the table with data from a file."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        dbshare.db.check_quota()
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        schema = db["tables"].get(tablename)
        if not schema:
            raise ValueError("no such table")
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    return flask.render_template("table/update.html", db=db, schema=schema)


@blueprint.route("/<name:dbname>/<name:tablename>/update/csv", methods=["POST"])
@utils.login_required
def update_csv(dbname, tablename):
    "Update the table with data from a CSV file."
    utils.check_csrf_token()
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    # Do not check quota; update should not be a problem...
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        csvfile = flask.request.files["csvfile"]
    except KeyError:
        raise ValueError("no CSV file provided")
    try:
        delimiter = flask.request.form.get("delimiter") or "comma"
        delimiter = flask.current_app.config["CSV_FILE_DELIMITERS"][delimiter]["char"]
    except KeyError:
        raise ValueError("invalid delimiter")
    try:
        nrows, count = update_csv_rows(db, schema, csvfile, delimiter)
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(
            flask.url_for(".insert", dbname=dbname, tablename=tablename)
        )
    utils.flash_message(f"{nrows} rows in file; {count} table rows updated.")
    return flask.redirect(flask.url_for(".rows", dbname=dbname, tablename=tablename))


@blueprint.route("/<name:dbname>/<name:tablename>/clone", methods=["GET", "POST"])
@utils.login_required
def clone(dbname, tablename):
    "Create a clone of the table."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        dbshare.db.check_quota()
    except ValueError as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))

    if utils.http_GET():
        return flask.render_template("table/clone.html", db=db, schema=schema)

    elif utils.http_POST():
        try:
            schema = copy.deepcopy(schema)
            schema["name"] = flask.request.form["name"]
            if schema.get("title"):
                schema["title"] = "Clone of " + schema["title"]
            with dbshare.db.DbSaver(db) as saver:
                saver.add_table(schema)
                colnames = ",".join(['"%(name)s"' % c for c in schema["columns"]])
                sql = 'INSERT INTO "%s" (%s) SELECT %s FROM "%s"' % (
                    schema["name"],
                    colnames,
                    colnames,
                    tablename,
                )
                saver.dbcnx.execute(sql)
                saver.update_table(schema)
        except (ValueError, sqlite3.Error) as error:
            utils.flash_error(error)
            return flask.redirect(
                flask.url_for(".clone", dbname=dbname, tablename=tablename)
            )
        return flask.redirect(
            flask.url_for(".rows", dbname=dbname, tablename=schema["name"])
        )


@blueprint.route("/<name:dbname>/<name:tablename>/download")
def download(dbname, tablename):
    "Download the rows in the table to a file."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    return flask.render_template("table/download.html", db=db, schema=schema)


@blueprint.route("/<name:dbname>/<name:tablename>/download.csv")
def download_csv(dbname, tablename):
    "Output a CSV file of the rows in the table."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    try:
        delimiter = flask.request.form.get("delimiter") or "comma"
        try:
            delimiter = flask.current_app.config["CSV_FILE_DELIMITERS"][delimiter][
                "char"
            ]
        except KeyError:
            raise ValueError("invalid delimiter")
        rowid = utils.to_bool(flask.request.args.get("rowid"))
        if utils.to_bool(flask.request.args.get("header")):
            header = [c["name"] for c in schema["columns"]]
            if rowid:
                header.insert(0, "rowid")
        else:
            header = None
        writer = utils.CsvWriter(header, delimiter=delimiter)
        colnames = ['"%(name)s"' % c for c in schema["columns"]]
        if rowid:
            colnames.insert(0, "rowid")
        dbcnx = dbshare.db.get_cnx(dbname)
        sql = 'SELECT %s FROM "%s"' % (",".join(colnames), tablename)
        writer.write_rows(utils.execute_timeout(dbcnx, sql))
    except (ValueError, SystemError, sqlite3.Error) as error:
        utils.flash_error(error)
        return flask.redirect(
            flask.url_for(".download", dbname=dbname, tablename=tablename)
        )
    response = flask.make_response(writer.getvalue())
    response.headers.set("Content-Type", constants.CSV_MIMETYPE)
    response.headers.set(
        "Content-Disposition", "attachment", filename=f"{tablename}.csv"
    )
    return response


@blueprint.route("/<name:dbname>/<name:tablename>/statistics")
def statistics(dbname, tablename):
    "Display statistics for the content of the table's columns."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][tablename]
    except KeyError:
        utils.flash_error("no such table")
        return flask.redirect(flask.url_for("db.display", dbname=dbname))
    compute_statistics(db, schema)
    return flask.render_template("table/statistics.html", db=db, schema=schema)


def get_row_values_errors(columns):
    "Return the values and errors from the form for a row given the columns."
    errors = {}
    values = []
    for column in columns:
        try:
            value = flask.request.form.get(column["name"])
            if not value:
                value = None
                if column["notnull"]:
                    raise ValueError("value required")
            elif column["type"] == constants.INTEGER:
                value = int(value)
            elif column["type"] == constants.REAL:
                value = float(value)
        except (ValueError, TypeError) as error:
            errors[column["name"]] = str(error)
        values.append(value)
    return tuple(values), errors


def get_csv_rows(schema, csvfile, delimiter, header):
    """Get rows from the CSV input file to insert into the given table.
    The order of the items in the rows must match the order of the columns.
    Raises ValueError if any problem.
    """
    lines = csvfile.read().decode("utf-8").split("\n")
    rows = list(csv.reader(lines, delimiter=delimiter))
    # Eliminate empty rows
    rows = [r for r in rows if r]
    if not rows:
        raise ValueError("empty CSV file")
    if header:
        header = [h.strip() for h in rows.pop(0)]
        try:
            for n, column in enumerate(schema["columns"]):
                if header[n] != column["name"]:
                    raise ValueError("header/column name mismatch")
        except IndexError as msg:
            raise ValueError(str(msg))
    try:
        for i, column in enumerate(schema["columns"]):
            type = column["type"]
            notnull = column["notnull"]
            if type == constants.INTEGER:
                for n, row in enumerate(rows):
                    value = row[i]
                    if value:
                        row[i] = int(value)
                    elif notnull:
                        raise ValueError("NULL disallowed")
                    else:
                        row[i] = None
            elif type == constants.REAL:
                for n, row in enumerate(rows):
                    value = row[i]
                    if value:
                        row[i] = float(value)
                    elif notnull:
                        raise ValueError("NULL disallowed")
                    else:
                        row[i] = None
            else:
                for n, row in enumerate(rows):
                    value = row[i]
                    if value:
                        row[i] = value
                    elif notnull:
                        raise ValueError("NULL disallowed")
                    else:
                        row[i] = None
    except (ValueError, TypeError, IndexError) as error:
        raise ValueError(
            "line %s, column %s (%s): %s" % (n + 1, i + 1, column["name"], str(error))
        )
    return rows


def insert_rows(db, schema, rows):
    "Insert the given rows into the given table."
    with dbshare.db.DbSaver(db) as saver:
        with saver.dbcnx:
            names = ",".join(['"%(name)s"' % c for c in schema["columns"]])
            values = ",".join("?" * len(schema["columns"]))
            sql = f"""INSERT INTO "{schema['name']}" ({names}) VALUES ({values})"""
            saver.dbcnx.executemany(sql, rows)
            saver.update_table(schema)


def update_csv_rows(db, schema, csvfile, delimiter):
    """Update the given table with the given CSV file.
    The CSV file must contain a header row. The primary key column(s)
    must be present. Only given column values will be updated.
    Raises ValueError if any problem.
    """
    lines = csvfile.read().decode("utf-8").split("\n")
    rows = list(csv.reader(lines, delimiter=delimiter))
    # Eliminate empty rows.
    rows = [r for r in rows if r]
    if len(rows) <= 1:
        raise ValueError("empty CSV file")
    # Figure out mapping of CSV row columns to table columns.
    header = [h.strip() for h in rows.pop(0)]
    primarykeys = set([c["name"] for c in schema["columns"] if c.get("primarykey")])
    columns = set([c["name"] for c in schema["columns"]])
    pkpos = {}
    for pos, name in enumerate(header):
        if name in primarykeys:
            pkpos[name] = pos
    if not pkpos:
        raise ValueError("no primary key in table")
    if len(primarykeys) != len(pkpos):
        raise ValueError("missing primary key column(s) in CSV file")
    colpos = {}
    for pos, name in enumerate(header):
        if name in primarykeys:
            continue
        if name not in columns:
            continue
        colpos[name] = pos
    if not colpos:
        raise ValueError("no columns in CSV file for update")
    setexpr = ",".join(['"%s"=?' % pk for pk in colpos.keys()])
    criteria = " AND ".join(['"%s"=?' % pk for pk in pkpos.keys()])
    sql = f"""UPDATE "{schema['name']}" SET {setexpr} WHERE {criteria}"""
    colpos = colpos.values()
    pkpos = pkpos.values()
    count = 0
    try:
        with dbshare.db.DbSaver(db) as saver:
            with saver.dbcnx:
                for rowpos, row in enumerate(rows):
                    values = [row[i] for i in colpos]
                    pkeys = [row[i] for i in pkpos]
                    cursor = saver.dbcnx.execute(sql, values + pkeys)
                    count += cursor.rowcount
    except sqlite3.Error as error:
        raise ValueError("row number %s; %s", (rowpos + 1, str(error)))
    return (len(rows), count)


def compute_statistics(db, schema):
    """Compute the stastistics for the data of the table's columns.
    Cache the results if the database is writeable.
    """
    # Skip if no columns.
    if len(schema["columns"]) == 0:
        return
    # Skip if statistics already present.
    if "statistics" in schema["columns"][0]:
        return

    # Recompute statistics and cache.
    dbcnx = dbshare.db.get_cnx(db["name"])
    for column in schema["columns"]:
        column["statistics"] = stats = {}
        sql = f'''SELECT "{column['name']}" FROM "{schema['name']}"'''
        values = [row[0] for row in dbcnx.execute(sql)]

        # Number of NULLs in the column.
        stats["nulls"] = {"title": "NULL values"}
        if column.get("notnull"):
            stats["nulls"]["value"] = False
            nonnull_values = values
        else:
            count = 0
            for value in values:
                if value is None:
                    count += 1
            stats["nulls"]["value"] = count
            if count:
                nonnull_values = [v for v in values if v is not None]
            else:
                nonnull_values = values
            stats["nonnulls"] = {
                "title": "Non-NULL values",
                "value": len(nonnull_values),
            }

        # Number of unique values in the column.
        stats["uniques"] = {"title": "Unique values"}
        if column.get("primarykey"):
            stats["uniques"]["value"] = True
        else:
            uniques = set(nonnull_values)
            stats["uniques"]["value"] = len(uniques)
            if len(uniques) < 9:
                stats["uniques"]["info"] = list(uniques)

        nonnull_values = sorted(nonnull_values)

        # Numerical min, max, mean, median
        if column["type"] in (constants.INTEGER, constants.REAL):
            if len(nonnull_values):
                stats["min"] = {"title": "Minimum", "value": nonnull_values[0]}
                mean = statistics_module.mean(nonnull_values)
                stats["mean"] = {"title": "Mean", "value": mean}
                stats["median"] = {
                    "title": "Median",
                    "value": statistics_module.median_low(nonnull_values),
                }
                stats["max"] = {"title": "Maximum", "value": nonnull_values[-1]}
                if len(nonnull_values) > 2:
                    stats["stdev"] = {
                        "title": "Standard deviation",
                        "value": statistics_module.stdev(nonnull_values, xbar=mean),
                    }

        # Lexical min, max
        if column["type"] == constants.TEXT:
            if len(nonnull_values):
                stats["min"] = {"title": "Lexical minimum", "value": nonnull_values[0]}
                stats["max"] = {"title": "Lexical maximum", "value": nonnull_values[-1]}
    if dbshare.db.has_write_access(db):
        with dbshare.db.DbSaver(db) as saver:
            saver.update_table(schema, reset_cache=False)
