"Redirect to table or view."

import flask

import dbshare.db


blueprint = flask.Blueprint("data", __name__)


@blueprint.route("/<name:dbname>/<name:dataname>")
def rows(dbname, dataname):
    "Redirect to display rows in the table or view."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        utils.flash_error(error)
        return flask.redirect(flask.url_for("home"))
    try:
        schema = db["tables"][dataname]
    except KeyError:
        try:
            schema = db["views"][dataname]
        except KeyError:
            utils.flash_error("no such table or view")
            return flask.redirect(flask.url_for("db.display", dbname=dbname))
        return flask.redirect(
            flask.url_for("view.rows", dbname=dbname, viewname=dataname)
        )
    return flask.redirect(
        flask.url_for("table.rows", dbname=dbname, tablename=dataname)
    )
