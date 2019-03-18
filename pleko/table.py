"Pleko table resources."

import flask

import pleko.master
from pleko import constants
from pleko import utils
from pleko.db import get_check_write
from pleko.user import login_required


blueprint = flask.Blueprint('table', __name__)

@blueprint.route('/<id:dbid>', methods=["GET", "POST"])
@login_required
def create(dbid):
    "Create a table with columns in the database."
    try:
        db = get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))
    if utils.is_method_GET():
        return flask.render_template('table/create.html', db=db)
    elif utils.is_method_POST():
        identifiers = set()
        columns = []
        for n in range(flask.current_app.config['TABLE_INITIAL_COLUMNS']):
            identifier = flask.request.form.get("column%sid" % n)
            if not identifier: break
            if not constants.IDENTIFIER_RX.match(identifier):
                raise ValueError("invalid identifier in column %s" % (n+1))
            if identifier in identifiers:
                raise ValueError("repeated identifier in column %s" % (n+1))
            identifiers.add(identifier)
            column = {'identifier': identifier}
            type = flask.request.form.get("column%stype" % n)
            if type not in constants.COLUMN_TYPES:
                raise ValueError("invalid type in column %s" % (n+1))
            column['type'] = type
            column['notnull'] = utils.to_bool(
                flask.request.form.get("column%snotnull" % n))
            columns.append(column)
        if not columns:
            raise ValueError('no columns defined')
        coldefs = []
        for column in columns:
            coldef = "{identifier} {type}".format(column)
            if column['primarykey']:
                coldef += ' PRIMARY KEY'
                %%%
