"Pleko plot endpoints."

import sqlite3

import flask

import pleko.db
import pleko.master
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('plot', __name__)

@blueprint.route('/<name:dbname>/<name:tvname>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname):
    "Create a plot of a table or view in the database."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/create.html', db=db)

    elif utils.is_method_POST():
        raise NotImplementedError
