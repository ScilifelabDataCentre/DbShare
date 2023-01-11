"About HTML endpoints."

import sqlite3
import sys

import flask
import http.client
import jinja2

import dbshare

from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint("about", __name__)


@blueprint.route("/contact")
def contact():
    "Display the contact information page."
    return flask.render_template(
        "about/contact.html", text=utils.get_site_text("contact.md")
    )


@blueprint.route("/gdpr")
def gdpr():
    "Display the personal data policy page."
    return flask.render_template("about/gdpr.html", text=utils.get_site_text("gdpr.md"))


@blueprint.route("/software")
def software():
    "Display software in system with links and version info."
    config = flask.current_app.config
    v = sys.version_info
    software = [
        ("DbShare", dbshare.__version__, constants.URL),
        ("Python", f"{v.major}.{v.minor}.{v.micro}", "https://www.python.org/"),
        ("Sqlite3", sqlite3.version, "https://www.sqlite.org/"),
        ("Flask", flask.__version__, "http://flask.pocoo.org/"),
        ("Jinja2", jinja2.__version__, "http://jinja.pocoo.org/docs"),
        ("Bootstrap", constants.BOOTSTRAP_VERSION, constants.BOOTSTRAP_URL),
        ("jQuery", constants.JQUERY_VERSION, constants.JQUERY_URL),
        (
            "jQuery.localtime",
            constants.JQUERY_LOCALTIME_VERSION,
            constants.JQUERY_LOCALTIME_URL,
        ),
        ("DataTables", constants.DATATABLES_VERSION, constants.DATATABLES_URL),
    ]
    return flask.render_template("about/software.html", software=software)


@blueprint.route("/settings")
@utils.admin_required
def settings():
    "Display the configuration settings."
    config = flask.current_app.config.copy()
    for key in ["SECRET_KEY", "MAIL_PASSWORD"]:
        if config.get(key):
            config[key] = "<hidden>"
    return flask.render_template("about/settings.html", items=sorted(config.items()))
