"View endpoints."

import copy
import sqlite3

import flask

import dbportal.db
import dbportal.table
import dbportal.user
from dbportal import constants
from dbportal import utils


blueprint = flask.Blueprint('view', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
@dbportal.user.login_required
def create(dbname):
    "Create a view of the data in the database."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    viewname = flask.request.values.get('name')
    title = flask.request.values.get('title')
    description = flask.request.values.get('description')
    # Do not check here.
    query = dbportal.query.get_query_from_request()

    if utils.http_GET():
        return flask.render_template('view/create.html',
                                     db=db,
                                     name=viewname,
                                     description=description,
                                     query=query)

    elif utils.http_POST():
        try:
            # Get again, with checking this time.
            query = dbportal.query.get_query_from_request(check=True)
            schema = {'name': viewname,
                      'title': title or None,
                      'description': description or None,
                      'query': query}
            with dbportal.db.DbContext(db) as ctx:
                ctx.add_view(schema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create',
                                                dbname=dbname,
                                                name=viewname,
                                                description=description,
                                                **schema['query']))
        return flask.redirect(flask.url_for('.rows', 
                                            dbname=dbname,
                                            viewname=viewname))

@blueprint.route('/<name:dbname>/<name:viewname>/edit', methods=['GET', 'POST'])
@dbportal.user.login_required
def edit(dbname, viewname):
    "Edit the view."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('view/edit.html', db=db, schema=schema)

    elif utils.http_POST():
        try:
            with dbportal.db.DbContext(db) as ctx:
                schema['title'] = flask.request.form.get('title') or None
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
    "Display rows in the view. Or delete the view."
    if utils.http_GET():
        try:
            db = dbportal.db.get_check_read(dbname, nrows=[str(viewname)])
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        has_write_access = dbportal.db.has_write_access(db)
        try:
            schema = db['views'][str(viewname)]
        except KeyError:
            flask.flash('no such view', 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        try:
            title = schema.get('title') or "View {}".format(viewname)
            visuals = utils.sorted_schema(db['visuals'].get(schema['name'], []))
            colnames = ['"%s"' % c for c in schema['query']['columns']]
            dbcnx = dbportal.db.get_cnx(dbname)
            sql = 'SELECT %s FROM "%s"' % (','.join(colnames), viewname)

            if viewname.ext is None or viewname.ext == 'html':
                limit = flask.current_app.config['MAX_NROWS_DISPLAY']
                if schema['nrows'] > limit:
                    sql += f" LIMIT {limit}"
                    utils.flash_message_limit(limit)
                rows = utils.execute_timeout(dbcnx, sql) # Maybe LIMIT imposed
                query = schema['query']
                sql = dbportal.query.get_sql_query(query) # No imposed LIMIT
                return flask.render_template('view/rows.html', 
                                             db=db,
                                             schema=schema,
                                             query=query,
                                             sql=sql,
                                             title=title,
                                             rows=rows,
                                             visuals=visuals,
                                             has_write_access=has_write_access)

            elif viewname.ext == 'csv':
                columns = [c['name'] for c in schema['columns']]
                writer = utils.CsvWriter(header=columns)
                try:
                    rows = utils.execute_timeout(dbcnx, sql)
                except SystemError:
                    flask.abort(504) # "Gateway timeout"; least bad status code
                writer.write_rows(rows)
                return flask.Response(writer.get(),
                                      mimetype=constants.CSV_MIMETYPE)

            elif viewname.ext == 'json':
                columns = [c['name'] for c in schema['columns']]
                try:
                    rows = utils.execute_timeout(dbcnx, sql)
                except SystemError:
                    flask.abort(504) # "Gateway timeout"; least bad status code
                return flask.jsonify(
                    {'$id': flask.request.url,
                     'title': title,
                     'visualizations': 
                     [{'name': v['name'],
                       'href': utils.get_url('visual.display',
                                             values={'dbname': dbname,
                                                     'visualname': v['name']})}
                      for v in visuals],
                     'data': [dict(zip(columns, row)) for row in rows]})
            else:
                flask.abort(406)

        except (SystemError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.schema',
                                                viewname=str(viewname)))

    elif utils.http_DELETE():
        try:
            db = dbportal.db.get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        try:
            with dbportal.db.DbContext(db) as ctx:
                ctx.delete_view(str(viewname))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:viewname>/schema')
def schema(dbname, viewname):
    "Display the schema for a view."
    try:
        db = dbportal.db.get_check_read(dbname, nrows=[viewname])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    sources = [dbportal.db.get_schema(db, name) for name in schema['sources']]
    # Special case: Create HTML links for sources, handling "AS" parts.
    html_from = schema['query']['from']
    for source in sources:
        if source['type'] == constants.TABLE:
            url = flask.url_for('table.rows',
                                dbname=dbname,
                                tablename=source['name'])
        else:
            url = flask.url_for('view.rows',
                                dbname=dbname,
                                viewname=source['name'])
        html = '<a href="%s">%s</a>' % (url, source['name'])
        html_from = html_from.replace(source['name'], html)
    return flask.render_template('view/schema.html',
                                 db=db,
                                 schema=schema,
                                 sources=sources,
                                 html_from=html_from)

@blueprint.route('/<name:dbname>/<name:viewname>/clone', 
                 methods=['GET', 'POST'])
@dbportal.user.login_required
def clone(dbname, viewname):
    "Create a clone of the view."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('view/clone.html', db=db, schema=schema)

    elif utils.http_POST():
        try:
            schema = copy.deepcopy(schema)
            schema['name'] = flask.request.form['name']
            with dbportal.db.DbContext(db) as ctx:
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
        db = dbportal.db.get_check_read(dbname)
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
        db = dbportal.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError:
        flask.flash('no such view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        delimiter = flask.request.form.get('delimiter') or 'comma'
        try:
            delimiter = flask.current_app.config['CSV_FILE_DELIMITERS'][delimiter]['char']
        except KeyError:
            raise ValueError('invalid delimiter')
        if utils.to_bool(flask.request.args.get('header')):
            header = schema['query']['columns']
        else:
            header = None
        writer = utils.CsvWriter(header, delimiter=delimiter)
        colnames = ['"%s"' % c for c in schema['query']['columns']]
        dbcnx = dbportal.db.get_cnx(dbname)
        sql = 'SELECT %s FROM "%s"' % (','.join(colnames), viewname)
        writer.add_rows(utils.execute_timeout(dbcnx, sql))
    except (ValueError, SystemError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.download',
                                            dbname=dbname,
                                            viewname=viewname))
    response = flask.make_response(writer.get())
    response.headers.set('Content-Type', constants.CSV_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename="%s.csv" % viewname)
    return response
