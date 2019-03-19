"Pleko table schema endpoints."

import flask

import pleko.db
from pleko import utils
from pleko.user import login_required


def get(cursor, tableid):
    """Get the schema for the given table given the cursor for the database.
    Raise ValueError if no such table."""
    sql = 'PRAGMA table_info("%s")' % tableid
    cursor.execute(sql)
    rows = list(cursor)
    if len(rows) == 0:
        raise ValueError('no such table in database')
    return {'id': tableid,
            'columns': [{'id': row[1],
                         'type': row[2],
                         'notnull': bool(row[3]),
                         'defaultvalue': row[4],
                         'primarykey': bool(row[5])}
                        for row in rows]}


blueprint = flask.Blueprint('schema', __name__)

@blueprint.route('/<id:dbid>/<id:tableid>', methods=['GET', 'POST', 'DELETE'])
@login_required
def table(dbid, tableid):
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        has_write_access = pleko.db.has_write_access(db)
        cnx = pleko.db.get_cnx(dbid)
        try:
            cursor = cnx.cursor()
            try:
                schema = get(cursor, tableid)
            except ValueError as error:
                flask.flash(str(error), 'error')
                return flask.redirect(flask.url_for('db.index', dbid=dbid))
            sql = "SELECT COUNT(*) FROM %s" % tableid
            cursor.execute(sql)
            nrows = cursor.fetchone()[0]
            return flask.render_template('schema/table.html',
                                         db=db,
                                         schema=schema,
                                         nrows=nrows,
                                         has_write_access=has_write_access)
        finally:
            cnx.close()

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        cnx = pleko.db.get_cnx(dbid)
        try:
            cursor = cnx.cursor()
            try:
                sql = "DROP TABLE %s" % tableid
                cursor.execute(sql)
            except sqlite3.Error as error:
                flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        finally:
            cnx.close()
