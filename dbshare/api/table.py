"Table API endpoints."

import http.client
import sqlite3

import flask
import jsonschema

import dbshare.db
import dbshare.schema.table
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint('api_table', __name__)

@blueprint.route('/<name:dbname>/<name:tablename>',
                 methods=['GET', 'PUT', 'DELETE'])
def table(dbname, tablename):
    """GET: Return the schema for the table.
    PUT: Create the table.
    DELETE: Delete the table.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            schema = db['tables'][tablename]
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        result = get_api(db, schema, complete=True)
        result.update(schema)
        result['indexes'] = [i for i in db['indexes'].values() 
                             if i['table'] == tablename]
        return flask.jsonify(utils.get_api(**result))

    elif utils.http_PUT():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            data = flask.request.get_json()
            if data is None: raise ValueError
            with dbshare.db.DbContext(db) as ctx:
                ctx.add_table(data)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(
            flask.url_for('api_table.table', dbname=dbname,tablename=tablename))

    elif utils.http_DELETE():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbContext(db) as ctx:
                ctx.delete_table(tablename)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return ('', http.client.NO_CONTENT)

@blueprint.route('/<name:dbname>/<name:tablename>/insert', methods=['POST'])
def insert(dbname, tablename):
    """POST: Insert table rows from JSON data into the table.
    """
    try:
        db = dbshare.db.get_check_write(dbname)
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    try:
        schema = db['tables'][tablename]
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    
    data = flask.request.get_json()
    if data is None:
        flask.abort(http.client.UNSUPPORTED_MEDIA_TYPE)
    try:
        jsonschema.validate(instance=data,
                            schema=dbshare.schema.table.schema_data)
    except jsonschema.ValidationError as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    columns = schema['columns']
    rows = []
    try:
        for pos, item in enumerate(data['data']):
            values = []
            for column in columns:
                try:
                    value = item[column['name']]
                except KeyError:
                    if column.get('notnull'):
                        raise ValueError(f"missing key '{column['name']}'"
                                         f" in item # {pos}")
                    value = None
                else:
                    try:
                        if column['type'] == constants.INTEGER: 
                            if not isinstance(value, int): raise TypeError
                        elif column['type'] == constants.REAL:
                            if not isinstance(value, (int, float)):
                                raise TypeError
                        elif column['type'] == constants.TEXT:
                            if not isinstance(value, str): raise TypeError
                        elif column['type'] == constants.BLOB:
                            raise TypeError
                    except TypeError:
                        raise ValueError(f"invalid type for '{column['name']}'"
                                         f" in item # {pos}")
                values.append(value)
            rows.append(values)
    except ValueError as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    with dbshare.db.DbContext(db) as ctx:
        try:
            with ctx.dbcnx:
                sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                      (tablename,
                       ','.join(['"%(name)s"' % c for c in columns]),
                       ','.join('?' * len(columns)))
                ctx.dbcnx.executemany(sql, rows)
                ctx.update_table_nrows(schema)
        except sqlite3.Error as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for('api_table.table', dbname=dbname,tablename=tablename))

def get_api(db, table, complete=False):
    "Return the API JSON for the table."
    url = utils.url_for('table.rows',
                        dbname=db['name'],
                        tablename=table['name'])
    result = {'name': table['name'],
              'title': table.get('title'),
              'database': {'href': utils.url_for('api_db.database',
                                                 dbname=db['name'])},
              'nrows': table['nrows'],
              'rows': {'href': url + '.json'},
              'data': {'href': url + '.csv',
                       'content_type': constants.CSV_MIMETYPE,
                       'format': 'csv'}
    }
    if complete:
        visuals = []
        for visual in db['visuals'].get(table['name'], []):
            url = utils.url_for('visual.display',
                                dbname=db['name'],
                                visualname=visual['name'])
            visuals.append({
                'name': visual['name'],
                'title': visual.get('title'),
                'specification': {'href': url + '.json'}})
        result['visualizations'] = visuals
    else:
        result['href'] = utils.url_for('api_table.table',
                                       dbname=db['name'],
                                       tablename=table['name'])
    return result
