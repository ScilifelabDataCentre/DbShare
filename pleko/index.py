"Pleko index endpoint."

import sqlite3

import flask

import pleko.db
import pleko.table
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('index', __name__)

@blueprint.route('/<id:dbid>/<id:tableid>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbid, tableid):
    "Create an index on the table in the database."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tableid]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))
    positions = list(range(len(schema['columns'])))

    if utils.is_method_GET():
        cnx = pleko.db.get_cnx(dbid)
        for table in db['tables'].values():
            table['nrows'] = pleko.db.get_nrows(table['id'], cnx)
        return flask.render_template('index/create.html',
                                     db=db,
                                     schema=schema,
                                     positions=positions)

    elif utils.is_method_POST():
        try:
            INDEX_PREFIX = "%s$index" % schema['id']
            ordinal = -1
            for ix in db['indexes']:
                if ix.startswith(INDEX_PREFIX):
                    ordinal = max(ordinal, int(ix['id'][len(INDEX_PREFIX):]))
            index = {'id': INDEX_PREFIX + str(ordinal+1),
                     'table': schema['id'],
                     'unique': utils.to_bool(flask.request.form.get('unique'))}
            index['columns'] = []
            for pos in positions:
                column = flask.request.form.get("position%i" % pos)
                if column:
                    index['columns'].append(column)
                else:
                    break
            with pleko.db.DbContext(db) as ctx:
                ctx.add_index(index)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(
                flask.url_for('.create', dbid=dbid, tableid=tableid))
        else:
            return flask.redirect(
                flask.url_for('table.schema', dbid=dbid, tableid=tableid))
        
# 'indexid' is not a proper identifier
@blueprint.route('/<id:dbid>/<indexid>/delete', methods=['POST', 'DELETE'])
@pleko.user.login_required
def delete(dbid, indexid):
    "Delete the index."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        for index in db['indexes'].values():
            if index['id'] == indexid:
                tableid = index['table']
                break
        else:
            raise ValueError('no such index in database')
        with pleko.db.DbContext(db) as ctx:
            ctx.delete_index(indexid)
    except (ValueError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))
    return flask.redirect(
        flask.url_for('table.schema', dbid=dbid, tableid=tableid))
 
