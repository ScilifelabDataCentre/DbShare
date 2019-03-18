"Pleko table schema endpoints."

import flask

import pleko.db
from pleko.user import login_required


def get(cursor, tableid):
    """Get the schema for the given table given the cursor for the database.
    Raise ValueError if no such table."""
    sql = 'PRAGMA table_info("%s")' % tableid
    cursor.execute(sql)
    rows = list(cursor)
    if len(rows) == 0:
        raise ValueError('no such table in database')
    return {'tableid': tableid,
            'columns': [{'columnid': row[1],
                         'type': row[2],
                         'notnull': bool(row[3]),
                         'defaultvalue': row[4],
                         'primarykey': bool(row[5])}
                        for row in rows]}


blueprint = flask.Blueprint('schema', __name__)

@blueprint.route('/<id:dbid>/<id:tableid>')
@login_required
def table(dbid, tableid):
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(db['dbid'])
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
                                     nrows=nrows)
    finally:
        cnx.close()
