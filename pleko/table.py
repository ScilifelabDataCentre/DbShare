"Pleko table endpoints."

import copy
import csv
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
        return flask.redirect(flask.url_for('home'))
    try:
        pleko.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('table/create.html', db=db)

    elif utils.is_method_POST():
        try:
            schema = {'name': flask.request.form.get('name'),
                      'description': flask.request.form.get('description')}
            schema['columns'] = []
            for n in range(flask.current_app.config['TABLE_INITIAL_COLUMNS']):
                name = flask.request.form.get("column%sname" % n)
                if not name: break
                if not constants.NAME_RX.match(name):
                    raise ValueError("invalid name in column %s" % (n+1))
                column = {'name': name.lower()}
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

@blueprint.route('/<name:dbname>/<nameext:tablename>',
                 methods=['GET', 'POST', 'DELETE'])
def rows(dbname, tablename):  # NOTE: tablename is a NameExt instance!
    "Display rows in the table."
    if utils.is_method_GET():
        try:
            db = pleko.db.get_check_read(dbname, nrows=[str(tablename)])
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        has_write_access = pleko.db.has_write_access(db)
        try:
            schema = db['tables'][str(tablename)]
        except KeyError:
            flask.flash('no such table', 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        columns = [c['name'] for c in schema['columns']]
        cnx = pleko.db.get_cnx(dbname)
        cursor = cnx.cursor()
        sql = 'SELECT rowid, %s FROM "%s"' % \
              (','.join(['"%s"' % c for c in columns]), tablename)

        if tablename.ext is None or tablename.ext == 'html':
            limit = flask.current_app.config['MAX_NROWS_DISPLAY']
            if schema['nrows'] > limit:
                sql += " LIMIT %s" % limit
                flask.flash('NOTE: The number of rows displayed'
                            ' is limited to %s.' % limit,
                            'message')
            cursor.execute(sql)
            visuals = utils.sorted_schema(db['visuals'].get(schema['name'], []))
            return flask.render_template('table/rows.html', 
                                         db=db,
                                         schema=schema,
                                         rows=list(cursor),
                                         visuals=visuals,
                                         has_write_access=has_write_access)

        elif tablename.ext == 'csv':
            cursor.execute(sql)
            writer = utils.CsvWriter(header=columns)
            writer.add_from_cursor(cursor, skip_rowid=True)
            return flask.Response(writer.get(), mimetype=constants.CSV_MIMETYPE)

        elif tablename.ext == 'json':
            cursor.execute(sql)
            return flask.jsonify({'$id': flask.request.url,
                                  'data': [dict(zip(columns, row[1:]))
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
                ctx.delete_table(str(tablename))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:tablename>/edit',
                 methods=['GET', 'POST'])
@pleko.user.login_required
def edit(dbname, tablename):
    "Edit the table metadata."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('table/edit.html', db=db, schema=schema)

    elif utils.is_method_POST():
        try:
            with pleko.db.DbContext(db) as ctx:
                schema['description'] = flask.request.form.get('description') or None
                ctx.update_table(schema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.schema',
                                            dbname=dbname,
                                            tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/empty', methods=['POST'])
@pleko.user.login_required
def empty(dbname, tablename):
    "Empty the table; delete all rows."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    try:
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        with dbcnx:
            sql = 'DELETE FROM "%s"' % schema['name']
            dbcnx.execute(sql)
    except sqlite3.Error as error:
        flask.flash(str(error), 'error')
    return flask.redirect(flask.url_for('.rows',
                                        dbname=dbname,
                                        tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/schema')
def schema(dbname, tablename):
    "Display the schema for a table."
    try:
        db = pleko.db.get_check_read(dbname, nrows=[tablename])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    indexes = [i for i in db['indexes'].values() if i['table'] == tablename]
    return flask.render_template(
        'table/schema.html',
        db=db,
        schema=schema,
        indexes=indexes,
        has_write_access=pleko.db.has_write_access(db))

@blueprint.route('/<name:dbname>/<name:tablename>/row',
                 methods=['GET', 'POST'])
def row_insert(dbname, tablename):
    "Insert a row into the table."
    try:
        db = pleko.db.get_check_write(dbname, nrows=[tablename])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        pleko.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('table/row_insert.html',
                                     db=db,
                                     schema=schema,
                                     values={})
    
    elif utils.is_method_POST():
        values, errors = get_row_values_errors(schema['columns'])
        if errors:
            for item in errors.items():
                flask.flash("%s: %s" % item, 'error')
            return flask.render_template('table/row_insert.html', 
                                         db=db,
                                         schema=schema,
                                         values=values)
        try:
            dbcnx = pleko.db.get_cnx(dbname, write=True)
            cursor = dbcnx.cursor()
            with dbcnx:
                sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                      (tablename,
                       ','.join(['"%(name)s"' % c for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                cursor.execute(sql, values)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
            return flask.render_template('table/row_insert.html', 
                                         db=db,
                                         schema=schema,
                                         values=values)
        flask.flash('Row inserted.')
        return flask.redirect(flask.url_for('.row_insert',
                                            dbname=dbname,
                                            tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/row/<int:rowid>',
                 methods=['GET', 'POST', 'DELETE'])
def row_edit(dbname, tablename, rowid):
    "Edit or delete a row into the table."
    try:
        db = pleko.db.get_check_write(dbname, nrows=[tablename])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    # Do not check for quota; a loop-hole, but let it slide...
    dbcnx = pleko.db.get_cnx(dbname)
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        cursor = dbcnx.cursor()
        sql = 'SELECT %s FROM "%s" WHERE rowid=?' % \
              (','.join(['"%(name)s"' % c for c in schema['columns']]),
               schema['name'])
        cursor.execute(sql, (rowid,))
        rows = list(cursor)
        if len(rows) != 1:
            flask.flash('no such row in table', 'error')
            return flask.redirect(flask.url_for('.rows',
                                                dbname=dbname,
                                                tablename=tablename))
        return flask.render_template('table/row_edit.html',
                                     db=db,
                                     schema=schema,
                                     row=rows[0],
                                     rowid=rowid)

    elif utils.is_method_POST():
        values, errors = get_row_values_errors(schema['columns'])
        if errors:
            for item in errors.items():
                flask.flash("%s: %s" % item, 'error')
            return flask.render_template('table/row_edit.html', 
                                         db=db,
                                         schema=schema,
                                         row=values,
                                         rowid=rowid)
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        cursor = dbcnx.cursor()
        try:
            with dbcnx:
                sql = 'UPDATE "%s" SET %s WHERE rowid=?' % \
                      (tablename,
                       ','.join(['"%(name)s"=?' %c for c in schema['columns']]))
                values = values + (rowid,)
                cursor.execute(sql, values)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        else:
            flask.flash('Row updated.')
        return flask.redirect(flask.url_for('.rows',
                                            dbname=dbname,
                                            tablename=tablename))

    elif utils.is_method_DELETE():
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        with dbcnx:
            sql = 'DELETE FROM "%s" WHERE rowid=?' % schema['name']
            dbcnx.execute(sql, (rowid,))
        return flask.redirect(flask.url_for('.rows',
                                            dbname=dbname,
                                            tablename=tablename))


@blueprint.route('/<name:dbname>/<name:tablename>/upload')
def upload(dbname, tablename):
    "Insert data from a file into the table."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        pleko.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('table/upload.html', db=db, schema=schema)

@blueprint.route('/<name:dbname>/<name:tablename>/upload/csv', methods=['POST'])
def upload_csv(dbname, tablename):
    "Insert data from a CSV file into the table."
    utils.check_csrf_token()
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        pleko.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        delimiter = flask.request.form.get('delimiter') or 'comma'
        try:
            delimiter = flask.current_app.config['CSV_FILE_DELIMITERS'][delimiter]['char']
        except KeyError:
            raise ValueError('invalid delimiter')
        csvfile = flask.request.files['csvfile']
        lines = csvfile.read().decode('utf-8').split('\n')
        print('delimiter', delimiter)
        records = list(csv.reader(lines, delimiter=delimiter))
        # Eliminate empty records
        records = [r for r in records if r]
        if not records:
            raise ValueError('empty CSV file')
        header = utils.to_bool(flask.request.form.get('header'))
        if header:
            header = records.pop(0)
            for n, column in enumerate(schema['columns']):
                if header[n] != column['name']:
                    raise ValueError('header/column name mismatch')
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
            sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                  (tablename,
                   ','.join(['"%(name)s"' % c for c in schema['columns']]),
                   ','.join('?' * len(schema['columns'])))
            cursor.executemany(sql, records)
        flask.flash("Inserted %s rows" % len(records), 'message')
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
        return flask.redirect(flask.url_for('home'))
    try:
        pleko.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
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
                colnames = ','.join(['"%(name)s"' % c 
                                     for c in schema['columns']])
                sql = 'INSERT INTO "%s" (%s) SELECT %s FROM "%s"' % \
                      (schema['name'],
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
    except KeyError:
        flask.flash('no such table', 'error')
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
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        delimiter = flask.request.form.get('delimiter') or 'comma'
        try:
            delimiter = flask.current_app.config['CSV_FILE_DELIMITERS'][delimiter]['char']
        except KeyError:
            raise ValueError('invalid delimiter')
        rowid = utils.to_bool(flask.request.args.get('rowid'))
        if utils.to_bool(flask.request.args.get('header')):
            header = [c['name'] for c in schema['columns']]
            if rowid:
                header.insert(0, 'rowid')
        else:
            header = None
        writer = utils.CsvWriter(header, delimiter=delimiter)
        colnames = ['"%(name)s"' % c for c in schema['columns']]
        if rowid:
            colnames.insert(0, 'rowid')
        cursor = pleko.db.get_cnx(dbname).cursor()
        sql = 'SELECT %s FROM "%s"' % (','.join(colnames), tablename)
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

def get_row_values_errors(columns):
    "Return the values and errors from the form for a row given the columns."
    errors = {}
    values = []
    for column in columns:
        try:
            value = flask.request.form.get(column['name'])
            if not value:
                value = None
                if column['notnull']:
                    raise ValueError('value required')
            elif column['type'] == constants.INTEGER:
                value = int(value)
            elif column['type'] == constants.REAL:
                value = float(value)
        except (ValueError, TypeError) as error:
            errors[column['name']] = str(error)
        values.append(value)
    return tuple(values), errors
