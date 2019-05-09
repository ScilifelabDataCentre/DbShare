"Table endpoints."

import copy
import csv
import sqlite3

import flask

import dbportal.db
import dbportal.user
from dbportal import constants
from dbportal import utils


blueprint = flask.Blueprint('table', __name__)
api_blueprint = flask.Blueprint('api_table', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'POST'])
@dbportal.user.login_required
def create(dbname):
    "Create a table with columns in the database."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbportal.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('table/create.html', db=db)

    elif utils.http_POST():
        try:
            schema = {'name': flask.request.form.get('name'),
                      'title': flask.request.form.get('title') or None,
                      'description': flask.request.form.get('description') or None,
                      'nrows': 0
            }
            schema['columns'] = []
            for n in range(flask.current_app.config['TABLE_INITIAL_COLUMNS']):
                name = flask.request.form.get(f"column{n}name")
                if not name: break
                if not constants.NAME_RX.match(name):
                    raise ValueError(f"invalid name in column {n+1}")
                column = {'name': name.lower()}
                type = flask.request.form.get(f"column{n}type")
                if type not in constants.COLUMN_TYPES:
                    raise ValueError(f"invalid type in column {n+1}")
                column['type'] = type
                column['primarykey'] = utils.to_bool(
                    flask.request.form.get(f"column{n}primarykey"))
                column['notnull'] = utils.to_bool(
                    flask.request.form.get(f"column{n}notnull"))
                column['unique'] = utils.to_bool(
                    flask.request.form.get(f"column{n}unique"))
                schema['columns'].append(column)
            with dbportal.db.DbContext(db) as ctx:
                ctx.add_table(schema)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.create', dbname=dbname))
        else:
            return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<nameext:tablename>')
def rows(dbname, tablename):  # NOTE: tablename is a NameExt instance!
    "Display the rows in the table."
    try:
        db = dbportal.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    has_write_access = dbportal.db.has_write_access(db)
    try:
        schema = db['tables'][str(tablename)]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        title = schema.get('title') or "Table {}".format(tablename)
        visuals = utils.sorted_schema(db['visuals'].get(schema['name'], []))
        columns = [c['name'] for c in schema['columns']]
        dbcnx = dbportal.db.get_cnx(dbname)
        sql = 'SELECT rowid, %s FROM "%s"' % \
              (','.join([f'"{c}"' for c in columns]), tablename)

        if tablename.ext in (None, 'html'):
            limit = flask.current_app.config['MAX_NROWS_DISPLAY']
            if schema['nrows'] > limit:
                sql += f" LIMIT {limit}"
                utils.flash_message_limit(limit)
            rows = utils.execute_timeout(dbcnx, sql)
            updateable = bool([c for c in schema['columns']
                               if c.get('primarykey')])
            return flask.render_template('table/rows.html', 
                                         db=db,
                                         schema=schema,
                                         title=title,
                                         rows=rows,
                                         visuals=visuals,
                                         updateable=updateable,
                                         has_write_access=has_write_access)

        elif tablename.ext == 'csv':
            writer = utils.CsvWriter(header=columns)
            try:
                rows = utils.execute_timeout(dbcnx, sql)
            except SystemError:
                flask.abort(504) # "Gateway timeout"; least bad status code
            writer.write_rows(rows, skip_rowid=True)
            return flask.Response(writer.get(),
                                  mimetype=constants.CSV_MIMETYPE)

        elif tablename.ext == 'json':
            try:
                rows = utils.execute_timeout(dbcnx, sql)
            except SystemError:
                flask.abort(504) # "Gateway timeout"; least bad status code
            return flask.jsonify(utils.get_api(
                name=tablename,
                title=title,
                schema={'href': 'XXX'},
                data=[dict(zip(columns, row[1:])) for row in rows]))
        else:
            flask.abort(406)

    except (SystemError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.schema',
                                            tablename=str(tablename)))

@blueprint.route('/<name:dbname>/<name:tablename>/edit',
                 methods=['GET', 'POST', 'DELETE'])
@dbportal.user.login_required
def edit(dbname, tablename):
    "Edit the table metadata. Or delete the table."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('table/edit.html', db=db, schema=schema)

    elif utils.http_POST():
        try:
            with dbportal.db.DbContext(db) as ctx:
                schema['title'] = flask.request.form.get('title') or None
                schema['description'] = flask.request.form.get('description') or None
                ctx.update_table(schema)
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.schema',
                                            dbname=dbname,
                                            tablename=tablename))

    elif utils.http_DELETE():
        try:
            with dbportal.db.DbContext(db) as ctx:
                ctx.delete_table(str(tablename))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:tablename>/empty', methods=['POST'])
@dbportal.user.login_required
def empty(dbname, tablename):
    "Empty the table; delete all rows."
    utils.check_csrf_token()
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    try:
        with dbportal.db.DbContext(db) as ctx:
            with ctx.dbcnx:
                sql = 'DELETE FROM "%s"' % schema['name']
                ctx.dbcnx.execute(sql)
                ctx.update_table_nrows(schema['name'])
    except sqlite3.Error as error:
        flask.flash(str(error), 'error')
    return flask.redirect(flask.url_for('.rows',
                                        dbname=dbname,
                                        tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/schema')
def schema(dbname, tablename):
    "Display the schema for a table."
    try:
        db = dbportal.db.get_check_read(dbname)
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
        has_write_access=dbportal.db.has_write_access(db))

@api_blueprint.route('/<name:dbname>/<name:tablename>')
def api_table(dbname, tablename):
    "The schema for a table."
    try:
        db = dbportal.db.get_check_read(dbname)
    except ValueError as error:
        flask.abort(404, message=str(error))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.abort(404)
    result = schema.copy()
    result['indexes'] = [i for i in db['indexes'].values() 
                         if i['table'] == tablename]
    result.update(get_api_table(db, schema, reduced=True))
    return flask.jsonify(utils.get_api(**result))

@blueprint.route('/<name:dbname>/<name:tablename>/row',
                 methods=['GET', 'POST'])
def row_insert(dbname, tablename):
    "Insert a row into the table."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbportal.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('table/row_insert.html',
                                     db=db,
                                     schema=schema,
                                     values={})
    
    elif utils.http_POST():
        values, errors = get_row_values_errors(schema['columns'])
        if errors:
            for item in errors.items():
                flask.flash("%s: %s" % item, 'error')
            return flask.render_template('table/row_insert.html', 
                                         db=db,
                                         schema=schema,
                                         values=values)
        try:
            with dbportal.db.DbContext(db) as ctx:
                sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                      (tablename,
                       ','.join(['"%(name)s"' % c for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                with ctx.dbcnx:
                    ctx.dbcnx.execute(sql, values)
                ctx.update_table_nrows(schema)
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
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    # Do not check for quota; a loop-hole, but let it slide...
    dbcnx = dbportal.db.get_cnx(dbname)
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        cursor = dbcnx.cursor()
        sql = 'SELECT %s FROM "%s" WHERE rowid=?' % \
              (','.join(['"%(name)s"' % c for c in schema['columns']]),
               schema['name'])
        cursor.execute(sql, (rowid,))
        rows = cursor.fetchall()
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

    elif utils.http_POST():
        values, errors = get_row_values_errors(schema['columns'])
        if errors:
            for item in errors.items():
                flask.flash("%s: %s" % item, 'error')
            return flask.render_template('table/row_edit.html', 
                                         db=db,
                                         schema=schema,
                                         row=values,
                                         rowid=rowid)
        try:
            with dbportal.db.DbContext(db) as ctx:
                with ctx.dbcnx:
                    names = ','.join(['"%(name)s"=?' %c 
                                      for c in schema['columns']])
                    sql = 'UPDATE "%s" SET %s WHERE rowid=?' % (tablename,names)
                    values = values + (rowid,)
                    ctx.dbcnx.execute(sql, values)
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        else:
            flask.flash('Row updated.')
        return flask.redirect(flask.url_for('.rows',
                                            dbname=dbname,
                                            tablename=tablename))

    elif utils.http_DELETE():
        with dbportal.db.DbContext(db) as ctx:
            with ctx.dbcnx:
                sql = 'DELETE FROM "%s" WHERE rowid=?' % schema['name']
                ctx.dbcnx.execute(sql, (rowid,))
                ctx.update_table_nrows(schema)
        return flask.redirect(flask.url_for('.rows',
                                            dbname=dbname,
                                            tablename=tablename))


@blueprint.route('/<name:dbname>/<name:tablename>/insert')
def insert(dbname, tablename):
    "Insert data from a file into the table."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbportal.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('table/insert.html', db=db, schema=schema)

@blueprint.route('/<name:dbname>/<name:tablename>/insert/csv', methods=['POST'])
def insert_csv(dbname, tablename):
    "Insert data from a CSV file into the table."
    utils.check_csrf_token()
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbportal.db.check_quota()
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
        records = list(csv.reader(lines, delimiter=delimiter))
        # Eliminate empty records
        records = [r for r in records if r]
        if not records:
            raise ValueError('empty CSV file')
        header = utils.to_bool(flask.request.form.get('header'))
        if header:
            header = [h.strip() for h in records.pop(0)]
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
        with dbportal.db.DbContext(db) as ctx:
            with ctx.dbcnx:
                sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                      (tablename,
                       ','.join(['"%(name)s"' % c for c in schema['columns']]),
                       ','.join('?' * len(schema['columns'])))
                ctx.dbcnx.executemany(sql, records)
                ctx.update_table_nrows(schema)
        flask.flash(f"Inserted {len(records)} rows.", 'message')
    except (ValueError, IndexError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.insert',
                                            dbname=dbname,
                                            tablename=tablename))
    return flask.redirect(flask.url_for('.rows',
                                        dbname=dbname,
                                        tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/update')
def update(dbname, tablename):
    "Update the table with data from a file."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbportal.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'].get(tablename)
        if not schema: raise ValueError('no such table')
        primarykeys = [c for c in schema['columns'] if c.get('primarykey')]
        if not primarykeys:
            raise ValueError('table has no primary key')
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('table/update.html', db=db, schema=schema)

@blueprint.route('/<name:dbname>/<name:tablename>/update/csv', methods=['POST'])
def update_csv(dbname, tablename):
    "Update the table with data from a CSV file."
    utils.check_csrf_token()
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    # Do not check quota; update should not be a problem...
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        recpos = None
        delimiter = flask.request.form.get('delimiter') or 'comma'
        try:
            delimiter = flask.current_app.config['CSV_FILE_DELIMITERS'][delimiter]['char']
        except KeyError:
            raise ValueError('invalid delimiter')
        csvfile = flask.request.files['csvfile']
        lines = csvfile.read().decode('utf-8').split('\n')
        records = list(csv.reader(lines, delimiter=delimiter))
        # Eliminate empty records.
        records = [r for r in records if r]
        if not records:
            raise ValueError('empty CSV file')
        # Figure out mapping of CSV record columns to table columns.
        header = [h.strip() for h in records.pop(0)]
        primarykeys = set([c['name'] for c in schema['columns']
                           if c.get('primarykey')])
        columns = set([c['name'] for c in schema['columns']])
        pkpos = {}
        for pos, name in enumerate(header):
            if name in primarykeys:
                pkpos[name] = pos
        if len(primarykeys) != len(pkpos):
            raise ValueError('missing primary key column(s) in CSV file')
        colpos = {}
        for pos, name in enumerate(header):
            if name in primarykeys: continue
            if name not in columns: continue
            colpos[name] = pos
        if not colpos:
            raise ValueError('no columns in CSV file for update')
        sql = 'UPDATE "%s" SET %s WHERE %s' % \
              (tablename,
               ','.join(['"%s"=?' % pk for pk in colpos.keys()]),
               ' AND '.join(['"%s"=?' % pk for pk in pkpos.keys()]))
        colpos = colpos.values()
        pkpos = pkpos.values()
        count = 0
        with dbportal.db.DbContext(db) as ctx:
            with ctx.dbcnx:
                for recpos, record in enumerate(records):
                    values = [record[i] for i in colpos]
                    pkeys = [record[i] for i in pkpos]
                    cursor = ctx.dbcnx.execute(sql, values+pkeys)
                    count += cursor.rowcount
        flask.flash(f"{len(records)} records; {count} rows updated.", 'message')
    except (ValueError, IndexError, sqlite3.Error) as error:
        if recpos is None:
            flask.flash(str(error), 'error')
        else:
            flask.flash("record number %s; %s" (recpos+1, str(error)), 'error')
        return flask.redirect(flask.url_for('.insert',
                                            dbname=dbname,
                                            tablename=tablename))
    return flask.redirect(flask.url_for('.rows',
                                        dbname=dbname,
                                        tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/clone', 
                 methods=['GET', 'POST'])
@dbportal.user.login_required
def clone(dbname, tablename):
    "Create a clone of the table."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        dbportal.db.check_quota()
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.flash('no such table', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('table/clone.html',
                                     db=db,
                                     schema=schema)

    elif utils.http_POST():
        try:
            schema = copy.deepcopy(schema)
            schema['name'] = flask.request.form['name']
            with dbportal.db.DbContext(db) as ctx:
                ctx.add_table(schema)
                colnames = ','.join(['"%(name)s"' % c 
                                     for c in schema['columns']])
                sql = 'INSERT INTO "%s" (%s) SELECT %s FROM "%s"' % \
                      (schema['name'],
                       colnames,
                       colnames,
                       tablename)
                ctx.dbcnx.execute(sql)
                ctx.update_table_nrows(schema)
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
        db = dbportal.db.get_check_read(dbname)
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
        db = dbportal.db.get_check_read(dbname)
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
        dbcnx = dbportal.db.get_cnx(dbname)
        sql = 'SELECT %s FROM "%s"' % (','.join(colnames), tablename)
        writer.write_rows(utils.execute_timeout(dbcnx, sql))
    except (ValueError, SystemError, sqlite3.Error) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.download',
                                            dbname=dbname,
                                            tablename=tablename))
    response = flask.make_response(writer.get())
    response.headers.set('Content-Type', constants.CSV_MIMETYPE)
    response.headers.set('Content-Disposition', 'attachment', 
                         filename=f"{tablename}.csv")
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

def get_api_table(db, table, reduced=False):
    "Return the API JSON for the table."
    if reduced:
        result = {}
    else:
        result = {'name': table['name'],
                  'title': table.get('title'),
                  'table': {'href': utils.url_for('api_table.api_table',
                                                  dbname=db['name'],
                                                  tablename=table['name'])}}
    visuals = {}
    for visual in db['visuals'].get(table['name'], []):
        url = utils.url_for('visual.display',
                            dbname=db['name'],
                            visualname=visual['name'])
        visuals[visual['name']] = {
            'title': visual.get('title'),
            'spec': {'href': url + '.json'},
            'display': {'href': url, 'format': 'html'}}
    url = utils.url_for('table.rows',
                        dbname=db['name'],
                        tablename=table['name'])
    result.update({
        'nrows': table['nrows'],
        'rows': {'href': url + '.json'},
        'data': {'href': url + '.csv', 'format': 'csv'},
        'display': {'href': url, 'format': 'html'},
        'visualizations': visuals})
    return result

