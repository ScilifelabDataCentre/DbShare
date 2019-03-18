"Pleko table endpoints."

import flask

import pleko.db
import pleko.master
from pleko import constants
from pleko import utils
from pleko.user import login_required


blueprint = flask.Blueprint('table', __name__)

@blueprint.route('/<id:dbid>', methods=["GET", "POST"])
@login_required
def create(dbid):
    "Create a table with columns in the database."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.index', dbid=dbid))
    if utils.is_method_GET():
        return flask.render_template('table/create.html', db=db)
    elif utils.is_method_POST():
        tableid = flask.request.form.get('tableid')
        if not tableid:
            raise ValueError('no table identifier given')
        if not constants.IDENTIFIER_RX.match(tableid):
            raise ValueError('invalid table identifier')
        cnx = pleko.db.get_cnx(dbid)
        try:
            cursor = cnx.cursor()
            sql = "SELECT COUNT(*) FROM sqlite_master WHERE name=?"
            cursor.execute(sql, (tableid,))
            if cursor.fetchone()[0] != 0:
                raise ValueError('table identifier already defined')
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
            primarykey = flask.request.form.get('columnprimarykey')
            if primarykey:
                try:
                    primarykey = int(primarykey)
                    if primarykey < 0: raise ValueError
                    if primarykey >= len(columns): raise ValueError
                    columns[primarykey]['primarykey'] = True
                except ValueError:
                    pass
            coldefs = []
            for column in columns:
                coldef = "{identifier} {type}".format(**column)
                if column.get('primarykey'):
                    coldef += ' PRIMARY KEY'
                if column['notnull']:
                    coldef += ' NOT NULL'
                coldefs.append(coldef)
            sql = "CREATE TABLE %s (%s)" % (tableid, ', '.join(coldefs))
            cursor.execute(sql)
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        finally:
            cnx.close()
