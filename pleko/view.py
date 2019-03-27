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

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
def create(dbname):
    "Create a view of the data in the database."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    query = pleko.query.get_query_from_request()
    cnx = pleko.db.get_cnx(dbname)

    if utils.is_method_GET():
        for table in db['tables'].values():
            table['nrows'] = pleko.db.get_nrows(table['name'], cnx)
        return flask.render_template('view/create.html', db=db, query=query)

    elif utils.is_method_POST():
        try:
            schema = {'name': flask.request.form.get('name'),
                      'query': pleko.query.get_query_from_request(check=True)}
            with pleko.db.DbContext(db) as ctx:
                ctx.add_view(schema)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(
                utils.get_absolute_url('.create',
                                       values=dict(dbname=dbname),
                                       query=schema['query']))
        else:
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        
@blueprint.route('/<name:dbname>/<name:viewname>/schema')
def schema(dbname, viewname):
    "Display the schema for a view."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    nrows = pleko.db.get_nrows(viewname, pleko.db.get_cnx(dbname))
    return flask.render_template('view/schema.html',
                                 db=db,
                                 schema=schema,
                                 nrows=nrows)

@blueprint.route('/<name:dbname>/<name:viewname>', 
                 methods=['GET', 'POST', 'DELETE'])
def rows(dbname, viewname):
    "Display rows in the view."
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        has_write_access = pleko.db.has_write_access(db)
        try:
            schema = db['views'][viewname]
        except KeyError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        try:
            cnx = pleko.db.get_cnx(dbname)
            cursor = cnx.cursor()
            sql = "SELECT * FROM %s" % viewname
            cursor.execute(sql)
            rows = list(cursor)
            if schema['query']['columns'][0] == '*':
                try:
                    columns = ["column%i" % (i+1) for i in range(len(rows[0]))]
                except IndexError:
                    columns = ['columns']
            else:
                columns = schema['query']['columns']
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.schema', viewname=viewname))
        return flask.render_template('view/rows.html', 
                                     db=db,
                                     schema=schema,
                                     rows=rows,
                                     columns=columns,
                                     has_write_access=has_write_access)

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        try:
            with pleko.db.DbContext(db) as ctx:
                ctx.delete_view(viewname)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:viewname>/clone', 
                 methods=['GET', 'POST'])
@pleko.user.login_required
def clone(dbname, viewname):
    "Create a clone of the view."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    try:
        schema = db['views'][viewname]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('view/clone.html',
                                     db=db,
                                     schema=schema)

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
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('view/download.html', db=db,schema=schema)

@blueprint.route('/<name:dbname>/<name:viewname>/csv')
def download_csv(dbname, viewname):
    "Output a CSV file of the rows in the view."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['views'][viewname]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        header = utils.to_bool(flask.request.args.get('header'))
        delimiter = flask.request.args.get('delimiter') or ','
        if delimiter == '<tab>':
            delimiter = '\t'
        elif delimiter == '<space>':
            delimiter = ' '
        if not delimiter in constants.CSV_DELIMITERS:
            raise ValueError('invalid CSV delimiter character')
        columns = schema['query']['columns']
        outfile = io.StringIO()
        writer = csv.writer(outfile, delimiter=delimiter)
        if header:
            writer.writerow(columns)
        cnx = pleko.db.get_cnx(dbname)
        cursor = cnx.cursor()
        sql = "SELECT %s FROM %s" % (','.join(columns), viewname)
        cursor.execute(sql)
        for row in cursor:
            writer.writerow(row)
    except (ValueError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.download',
                                            dbname=dbname,
                                            viewname=viewname))
    outfile.seek(0)
    response = flask.make_response(outfile.read())
    response.headers.set('Content-Type', constants.CSV_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename="%s.csv" % viewname)
    return response
