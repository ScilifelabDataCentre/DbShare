"Pleko view endpoint."

import copy
import csv
import io
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
        return flask.redirect(flask.url_for('home'))
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
            return flask.redirect(flask.url_for('home'))
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
            return flask.redirect(flask.url_for('home'))
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
            schema = copy.deepcopy(schema)
            schema['id'] = flask.request.form['id']
            with pleko.db.DbContext(db) as ctx:
                ctx.add_view(schema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone',
                                                dbid=dbid,
                                                viewid=viewid))
        return flask.redirect(flask.url_for('.rows',
                                            dbid=dbid,
                                            viewid=schema['id']))

@blueprint.route('/<id:dbid>/<id:viewid>/download')
def download(dbid, viewid):
    "Download the rows in the view to a file."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewid]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))
    return flask.render_template('view/download.html', db=db,schema=schema)

@blueprint.route('/<id:dbid>/<id:viewid>/csv')
def download_csv(dbid, viewid):
    "Output a CSV file of the rows in the view."
    try:
        db = pleko.db.get_check_read(dbid)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewid]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbid=dbid))
    try:
        header = utils.to_bool(flask.request.args.get('header'))
        delimiter = flask.request.args.get('delimiter') or ','
        if delimiter == '<tab>':
            delimiter = '\t'
        elif delimiter == '<space>':
            delimiter = ' '
        if not delimiter in constants.CSV_DELIMITERS:
            raise ValueError('invalid CSV delimiter character')
        columns = schema['select']['columns']
        outfile = io.StringIO()
        writer = csv.writer(outfile, delimiter=delimiter)
        if header:
            writer.writerow(columns)
        cnx = pleko.db.get_cnx(dbid)
        cursor = cnx.cursor()
        sql = "SELECT %s FROM %s" % (','.join(columns), viewid)
        cursor.execute(sql)
        for row in cursor:
            writer.writerow(row)
    except (ValueError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.download',
                                            dbid=dbid,
                                            viewid=viewid))
    outfile.seek(0)
    response = flask.make_response(outfile.read())
    response.headers.set('Content-Type', constants.CSV_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename="%s.csv" % viewid)
    return response
