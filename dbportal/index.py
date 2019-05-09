"Index endpoints."

import sqlite3

import flask

import dbportal.db
import dbportal.table
from dbportal import constants
from dbportal import utils


blueprint = flask.Blueprint('index', __name__)

@blueprint.route('/<name:dbname>/<name:tablename>', methods=['GET', 'POST'])
@dbportal.user.login_required
def create(dbname, tablename):
    "Create an index on the table in the database."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    positions = list(range(len(schema['columns'])))

    if utils.http_GET():
        dbportal.db.set_nrows(db, targets=db['tables'].keys())
        return flask.render_template('index/create.html',
                                     db=db,
                                     schema=schema,
                                     positions=positions)

    elif utils.http_POST():
        try:
            prefix = constants.INDEX_PREFIX_TEMPLATE % schema['name']
            ordinal = -1
            for ix in db['indexes']:
                if ix.startswith(prefix):
                    try:
                        ordinal = max(ordinal, int(ix['name'][len(prefix):]))
                    except (ValueError, TypeError, IndexError):
                        pass
            index = {'name': prefix + str(ordinal+1),
                     'table': schema['name'],
                     'unique': utils.to_bool(flask.request.form.get('unique'))}
            index['columns'] = []
            for pos in positions:
                column = flask.request.form.get("position%i" % pos)
                if column:
                    index['columns'].append(column)
                else:
                    break
            with dbportal.db.DbContext(db) as ctx:
                ctx.add_index(index)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(
                flask.url_for('.create', dbname=dbname, tablename=tablename))
        else:
            return flask.redirect(flask.url_for('table.schema',
                                                dbname=dbname,
                                                tablename=tablename))
        
# 'indexname' is not a proper name
@blueprint.route('/<name:dbname>/<indexname>/delete',
                 methods=['POST', 'DELETE'])
@dbportal.user.login_required
def delete(dbname, indexname):
    "Delete the index."
    utils.check_csrf_token()
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        for index in db['indexes'].values():
            if index['name'] == indexname:
                tablename = index['table']
                break
        else:
            raise ValueError('no such index in database')
        with dbportal.db.DbContext(db) as ctx:
            ctx.delete_index(indexname)
    except (ValueError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))
    return flask.redirect(
        flask.url_for('table.schema', dbname=dbname, tablename=tablename))
 
