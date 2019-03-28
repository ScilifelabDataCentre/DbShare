"Pleko table endpoints."

import copy
import sqlite3

import flask

import pleko.db
import pleko.master
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('table', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname):
    "Create a table with columns in the database."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('table/create.html', db=db)

    elif utils.is_method_POST():
        try:
            schema = {'name': flask.request.form.get('name')}
            schema['columns'] = []
            for n in range(flask.current_app.config['TABLE_INITIAL_COLUMNS']):
                name = flask.request.form.get("column%sname" % n)
                if not name: break
                if not constants.NAME_RX.match(name):
                    raise ValueError("invalid name in column %s" % (n+1))
                column = {'name': name}
                type = flask.request.form.get("column%stype" % n)
                if type not in constants.COLUMN_TYPES:
                    raise ValueError("invalid type in column %s" % (n+1))
                column['type'] = type
                column['primarykey'] = utils.to_bool(
                    flask.request.form.get("column%sprimarykey" % n))
                column['notnull'] = utils.to_bool(
                    flask.request.form.get("column%snotnull" % n))
                column['unique'] = utils.to_bool(
                    flask.request.form.get("column%sunique" % n))
                schema['columns'].append(column)
            with pleko.db.DbContext(db) as ctx:
                ctx.add_table(schema)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create', dbname=dbname))
        else:
            return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:tablename>/schema')
def schema(dbname, tablename):
    "Display the schema for a table."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    has_write_access = pleko.db.has_write_access(db)
    nrows = pleko.db.get_nrows(tablename, pleko.db.get_cnx(dbname))
    indexes = [i for i in db['indexes'].values() if i['table'] == tablename]
    return flask.render_template('table/schema.html',
                                 db=db,
                                 schema=schema,
                                 nrows=nrows,
                                 indexes=indexes,
                                 has_write_access=has_write_access)

@blueprint.route('/<name:dbname>/<nameext:tablename>',
                 methods=['GET', 'POST', 'DELETE'])
def rows(dbname, tablename):    # NOTE: tablename is a NameExt instance!
    "Display rows in the table."
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        has_write_access = pleko.db.has_write_access(db)
        try:
            schema = db['tables'][str(tablename)]
        except KeyError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        columns = [c['name'] for c in schema['columns']]
        cnx = pleko.db.get_cnx(dbname)
        cursor = cnx.cursor()
        sql = "SELECT * FROM %s" % tablename
        cursor.execute(sql)
        if tablename.ext is None or tablename.ext == 'html':
            return flask.render_template('table/rows.html', 
                                         db=db,
                                         schema=schema,
                                         rows=list(cursor),
                                         has_write_access=has_write_access)
        elif tablename.ext == 'csv':
            writer = utils.CsvWriter(header=columns)
            writer.add_from_cursor(cursor)
            return flask.Response(writer.get(), mimetype=constants.CSV_MIMETYPE)
        elif tablename.ext == 'json':
            return flask.jsonify({'$id': flask.request.url,
                                  'data': [dict(zip(columns, row))
                                           for row in cursor]})

    elif utils.is_method_DELETE():
        try:
            db = pleko.db.get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        try:
            with pleko.db.DbContext(db) as ctx:
                ctx.delete_table(str(tablename))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:tablename>/row',
                 methods=['GET', 'POST'])
def row(dbname, tablename):
    "Add a row to the table."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.is_method_GET():
        try:
            schema = db['tables'][tablename]
        except KeyError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.render_template('table/row.html', 
                                     db=db,
                                     schema=schema)
    
    elif utils.is_method_POST():
        try:
            schema = db['tables'][tablename]
        except KeyError as error:
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        errors = {}
        values = []
        for column in schema['columns']:
            try:
                value = flask.request.form.get(column['name'])
                if not value:
                    if column['notnull']:
                        raise ValueError('value required for')
                    else:
                        value = None
                elif column['type'] == constants.INTEGER:
                    value = int(value)
                elif column['type'] == constants.REAL:
                    value = float(value)
                values.append(value)
            except (ValueError, TypeError) as error:
                errors[column['name']] = str(error)
        if errors:
            for item in errors.items():
                flask.flash("%s: %s" % item, 'error')
            return flask.render_template('table/row.html', 
                                         db=db,
                                         schema=schema)
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        cursor = dbcnx.cursor()
        try:
            with dbcnx:
                sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                      (tablename,
                       ','.join([c['name'] for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                cursor.execute(sql, values)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.row',
                                                dbname=dbname,
                                                tablename=tablename))
        else:
            flask.flash("%s rows in table" %
                        pleko.db.get_nrows(tablename ,dbcnx),
                        'message')
            return flask.redirect(flask.url_for('.row',
                                                dbname=dbname,
                                                tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/upload')
def upload(dbname, tablename):
    "Add data from a file to the table."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('table/upload.html', db=db, schema=schema)

@blueprint.route('/<name:dbname>/<name:tablename>/upload/csv', methods=['POST'])
def upload_csv(dbname, tablename):
    "Add data from a CSV file to the table."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        csvfile = flask.request.files['csvfile']
        lines = csvfile.read().decode('utf-8').split('\n')
        records = list(csv.reader(lines))
        header = records.pop(0)
        for n, column in enumerate(schema['columns']):
            if header[n] != column['name']:
                raise ValueError('header/column name mismatch')
        # Eliminate empty records
        records = [r for r in records if r]
        try:
            for i, column in enumerate(schema['columns']):
                type = column['type']
                notnull = column['notnull']
                if type == constants.INTEGER:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value:
                            record[i] = int(value)
                        elif notnull:
                            raise ValueError('NULL disallowed')
                        else:
                            record[i] = None
                elif type == constants.REAL:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value:
                            record[i] = float(value)
                        elif notnull:
                            raise ValueError('NULL disallowed')
                        else:
                            record[i] = None
                else:
                    for n, record in enumerate(records):
                        value = record[i]
                        if value:
                            record[i] = value
                        elif notnull:
                            raise ValueError('NULL disallowed')
                        else:
                            record[i] = None
        except (ValueError, TypeError, IndexError) as error:
            raise ValueError("line %s, column %s (%s): %s" %
                             (n+1, i+1, column['name'], str(error)))
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        cursor = dbcnx.cursor()
        with dbcnx:
            sql = "INSERT INTO %s (%s) VALUES (%s)" % \
                  (tablename,
                   ','.join([c['name'] for c in schema['columns']]),
                   ','.join('?' * len(schema['columns'])))
            cursor.executemany(sql, records)
        flask.flash("Added %s rows" % len(records), 'message')
    except (ValueError, IndexError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.upload',
                                            dbname=dbname,
                                            tablename=tablename))
    return flask.redirect(flask.url_for('.rows',
                                        dbname=dbname,
                                        tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/clone', 
                 methods=['GET', 'POST'])
@pleko.user.login_required
def clone(dbname, tablename):
    "Create a clone of the table."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('table/clone.html',
                                     db=db,
                                     schema=schema)

    elif utils.is_method_POST():
        try:
            schema = copy.deepcopy(schema)
            schema['name'] = flask.request.form['name']
            with pleko.db.DbContext(db) as ctx:
                ctx.add_table(schema)
            dbcnx = ctx.dbcnx
            cursor = dbcnx.cursor()
            with dbcnx:
                colnames = ','.join([c['name'] for c in schema['columns']])
                sql = "INSERT INTO %s (%s) SELECT %s FROM %s" % (schema['name'],
                                                                 colnames,
                                                                 colnames,
                                                                 tablename)
                dbcnx.execute(sql)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.clone',
                                                dbname=dbname,
                                                tablename=tablename))
        return flask.redirect(flask.url_for('.rows',
                                            dbname=dbname,
                                            tablename=schema['name']))

@blueprint.route('/<name:dbname>/<name:tablename>/download')
def download(dbname, tablename):
    "Download the rows in the table to a file."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('table/download.html', db=db,schema=schema)

@blueprint.route('/<name:dbname>/<name:tablename>/download.csv')
def download_csv(dbname, tablename):
    "Output a CSV file of the rows in the table."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        columns = [c['name'] for c in schema['columns']]
        if utils.to_bool(flask.request.args.get('header')):
            header = columns
        else:
            header = None
        writer = utils.CsvWriter(header,
                                 delimiter=flask.request.args.get('delimiter'))
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        cursor = dbcnx.cursor()
        sql = "SELECT %s FROM %s" % (','.join(columns), tablename)
        cursor.execute(sql)
        writer.add_from_cursor(cursor)
    except (ValueError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.download',
                                            dbname=dbname,
                                            tablename=tablename))
    response = flask.make_response(writer.get())
    response.headers.set('Content-Type', constants.CSV_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename="%s.csv" % tablename)
    return response
