"Pleko rows endpoints."

import flask

import pleko.db
import pleko.schema


blueprint = flask.Blueprint('rows', __name__)

@blueprint.route('/<id:dbid>/<id:tableid>')
def index(dbid, tableid):
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    cnx = pleko.db.get_cnx(dbid)
    try:
        cursor = cnx.cursor()
        try:
            schema = pleko.schema.get(cursor, tableid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.index', dbid=dbid))
        sql = "SELECT * FROM %s" % tableid
        cursor.execute(sql)
        rows = list(cursor)
        return flask.render_template('rows/index.html', 
                                     db=db,
                                     schema=schema,
                                     rows=rows,
                                     nrows=len(rows)) # XXX remove
    finally:
        cnx.close()
