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

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname):
    "Create a view of the data in the database."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    viewname = flask.request.values.get('name')
    description = flask.request.values.get('description')
    # Do not check here.
    query = pleko.query.get_query_from_request()

    if utils.is_method_GET():
        return flask.render_template('view/create.html',
                                     db=db,
                                     name=viewname,
                                     description=description,
                                     query=query)

    elif utils.is_method_POST():
        try:
            # Get again, with checking this time.
            query = pleko.query.get_query_from_request(check=True)
            schema = {'name': viewname,
                      'description': description,
                      'query': query}
            with pleko.db.DbContext(db) as ctx:
                ctx.add_view(schema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create',
                                                dbname=dbname,
                                                name=viewname,
                                                description=description,
                                                **schema['query']))
        else:
            return flask.redirect(flask.url_for('.rows', 
                                                dbname=dbname,
                                                viewname=viewname))

@blueprint.route('/<name:dbname>(<name:viewname>/edit', methods=['GET', 'POST'])
@pleko.user.login_required
def edit(dbname, viewname):
    "Edit the view."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('view/edit.html', db=db, schema=schema)

    elif utils.is_method_POST():
        try:
            with pleko.db.DbContext(db) as ctx:
                schema['description'] = flask.request.form.get('description') or None
                ctx.update_view(schema)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.edit',
                                                dbname=dbname,
                                                viewname=viewname))
        else:
            return flask.redirect(flask.url_for('.rows', 
                                                dbname=dbname,
                                                viewname=viewname))

@blueprint.route('/<name:dbname>/<nameext:viewname>', 
                 methods=['GET', 'POST', 'DELETE'])
def rows(dbname, viewname):     # NOTE: viewname is a NameExt instance!
    "Display rows in the view."
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        has_write_access = pleko.db.has_write_access(db)
        try:
            schema = db['views'][str(viewname)]
        except KeyError:
            flask.flash('no such view', 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        try:
            dbcnx = pleko.db.get_cnx(dbname)
            cursor = dbcnx.cursor()
            sql = 'SELECT * FROM "%s"' % viewname
            cursor.execute(sql)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.schema',
                                                viewname=str(viewname)))
        columns = [c['name'] for c in schema['columns']]
        if viewname.ext is None or viewname.ext == 'html':
            visuals = utils.sorted_schema(db['visuals'].get(schema['name'], []))
            query = schema['query']
            return flask.render_template('view/rows.html', 
                                         db=db,
                                         schema=schema,
                                         query=query,
                                         sql=pleko.query.get_sql_query(query),
                                         rows=list(cursor),
                                         visuals=visuals,
                                         has_write_access=has_write_access)
        elif viewname.ext == 'csv':
            writer = utils.CsvWriter(header=columns)
            writer.add_from_cursor(cursor)
            return flask.Response(writer.get(), mimetype=constants.CSV_MIMETYPE)
        elif viewname.ext == 'json':
            return flask.jsonify({'$id': flask.request.url,
                                  'data': [dict(zip(columns, row))
                                           for row in cursor]})
        else:
            flask.abort(406)

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        try:
            with pleko.db.DbContext(db) as ctx:
                ctx.delete_view(str(viewname))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:viewname>/schema')
def schema(dbname, viewname):
    "Display the schema for a view."
    try:
        db = pleko.db.get_check_read(dbname, nrows=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    sources = [pleko.db.get_schema(db, name) for name in schema['sources']]
    return flask.render_template('view/schema.html',
                                 db=db,
                                 schema=schema,
                                 sources=sources)

@blueprint.route('/<name:dbname>/<name:viewname>/clone', 
                 methods=['GET', 'POST'])
@pleko.user.login_required
def clone(dbname, viewname):
    "Create a clone of the view."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('view/clone.html', db=db, schema=schema)

    elif utils.is_method_POST():
        try:
            schema = copy.deepcopy(schema)
            schema['name'] = flask.request.form['name']
            with pleko.db.DbContext(db) as ctx:
                ctx.add_view(schema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone',
                                                dbname=dbname,
                                                viewname=viewname))
        return flask.redirect(flask.url_for('.rows',
                                            dbname=dbname,
                                            viewname=schema['name']))

@blueprint.route('/<name:dbname>/<name:viewname>/download')
def download(dbname, viewname):
    "Download the rows in the view to a file."
    try:
        db = pleko.db.get_check_read(dbname, nrows=False)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('view/download.html', db=db,schema=schema)

@blueprint.route('/<name:dbname>/<name:viewname>/csv')
def download_csv(dbname, viewname):
    "Output a CSV file of the rows in the view."
    try:
        db = pleko.db.get_check_read(dbname, nrows=False)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        colnames = schema['query']['columns']
        if utils.to_bool(flask.request.args.get('header')):
            header = colnames
        else:
            header = None
        writer = utils.CsvWriter(header,
                                 delimiter=flask.request.args.get('delimiter'))
        dbcnx = pleko.db.get_cnx(dbname)
        cursor = dbcnx.cursor()
        sql = 'SELECT %s FROM "%s"' % (','.join(['"%s"' % c for c in colnames]),
                                       viewname)
        cursor.execute(sql)
        writer.add_from_cursor(cursor)
    except (ValueError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.download',
                                            dbname=dbname,
                                            viewname=viewname))
    response = flask.make_response(writer.get())
    response.headers.set('Content-Type', constants.CSV_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename="%s.csv" % viewname)
    return response
