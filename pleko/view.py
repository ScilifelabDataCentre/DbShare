"Pleko view endpoint."

import copy
import sqlite3

import flask

import pleko.db
import pleko.table
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('view', __name__)

@blueprint.route('/<id:dbid>', methods=['GET', 'POST'])
def create(dbid):
    "Create a view of the data in the database."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    select = {'select': flask.request.args.get('select') or '',
              'from': flask.request.args.get('from') or '',
              'where': flask.request.args.get('where') or '',
              'orderby': flask.request.args.get('orderby') or ''}
    try:
        select['limit'] = flask.request.args['limit']
        if select['limit'].lower() == 'none':
            select['limit'] = None
    except KeyError:
        select['limit']= flask.current_app.config['QUERY_DEFAULT_LIMIT']
    cnx = pleko.db.get_cnx(dbid)

    if utils.is_method_GET():
        for table in db['tables'].values():
            table['nrows'] = pleko.db.get_nrows(table['id'], cnx)
            return flask.render_template('view/create.html',
                                         db=db,
                                         select=select,
                                         tables=sorted(db['tables'].values(),
                                                       key=lambda t: t['id']))

    elif utils.is_method_POST():
        try:
            schema = {'id': flask.request.form.get('id')}
            if not schema['id']:
                raise ValueError('no view identifier given')
            if not constants.IDENTIFIER_RX.match(schema['id']):
                raise ValueError('invalid view identifier')
            cursor = cnx.cursor()
            sql = "SELECT COUNT(*) FROM sqlite_master WHERE name=? AND type=?"
            cursor.execute(sql, (schema['id'], 'view'))
            if cursor.fetchone()[0] != 0:
                raise ValueError('view identifier already in use')
            schema['select'] = pleko.query.get_select_from_form()
            with pleko.db.DbContext(db) as ctx:
                ctx.add_view(schema)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create', dbid=dbid))
        else:
            return flask.redirect(flask.url_for('db.home', dbid=dbid))
        
@blueprint.route('/<id:dbid>/<id:viewid>/schema')
def schema(dbid, viewid):
    "Display the schema for a view."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    try:
        schema = db['views'][viewid]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))
    nrows = pleko.db.get_nrows(viewid, pleko.db.get_cnx(dbid))
    return flask.render_template('view/schema.html',
                                 db=db,
                                 schema=schema,
                                 nrows=nrows)

@blueprint.route('/<id:dbid>/<id:viewid>', methods=['GET', 'POST', 'DELETE'])
def rows(dbid, viewid):
    "Display rows in the view."
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        has_write_access = pleko.db.has_write_access(db)
        try:
            schema = db['views'][viewid]
        except KeyError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbid=dbid))
        try:
            cnx = pleko.db.get_cnx(dbid)
            cursor = cnx.cursor()
            sql = "SELECT * FROM %s" % viewid
            cursor.execute(sql)
            rows = list(cursor)
            if schema['select']['columns'][0] == '*':
                try:
                    columns = ["column%i" % (i+1) for i in range(len(rows[0]))]
                except IndexError:
                    columns = ['columns']
            else:
                columns = schema['select']['columns']
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.schema', viewid=viewid))
        return flask.render_template('view/rows.html', 
                                     db=db,
                                     schema=schema,
                                     rows=rows,
                                     columns=columns,
                                     has_write_access=has_write_access)

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbid)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))
        try:
            with pleko.db.DbContext(db) as ctx:
                ctx.delete_view(viewid)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))

@blueprint.route('/<id:dbid>/<id:viewid>/clone', methods=['GET', 'POST'])
@pleko.user.login_required
def clone(dbid, viewid):
    "Create a clone of the view."
    try:
        db = pleko.db.get_check_write(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))

    try:
        schema = db['views'][viewid]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))

    if utils.is_method_GET():
        return flask.render_template('view/clone.html',
                                     db=db,
                                     schema=schema)

    elif utils.is_method_POST():
        try:
            newschema = copy.deepcopy(schema)
            newschema['id'] = flask.request.form['id']
            with pleko.db.DbContext(db) as ctx:
                ctx.add_view(newschema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone',
                                                dbid=dbid,
                                                viewid=viewid))
        return flask.redirect(flask.url_for('.rows',
                                            dbid=dbid,
                                            viewid=newschema['id']))
