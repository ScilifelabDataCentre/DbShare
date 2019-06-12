"Table API endpoints."

import io
import http.client
import sqlite3

import flask
import jsonschema

import dbshare.db
import dbshare.table
import dbshare.schema.table

from .. import constants
from .. import utils


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
        result = get_json(db, schema, complete=True)
        result.update(schema)
        result['indexes'] = [i for i in db['indexes'].values() 
                             if i['table'] == tablename]
        return flask.jsonify(utils.get_json(**result))

    elif utils.http_PUT():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbContext(db) as ctx:
                ctx.add_table(flask.request.get_json())
        except (jsonschema.ValidationError, ValueError) as error:
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
    "POST: Insert table rows from JSON or CSV data into the table."
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
    
    try:
        # JSON input data
        if flask.request.is_json:
            try:
                data = flask.request.get_json()
                utils.json_validate(data, dbshare.schema.table.input)
            except jsonschema.ValidationError as error:
                utils.abort_json(http.client.BAD_REQUEST, error)
            columns = schema['columns']
            # Check validity of values in input data.
            rows = []
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
                            raise ValueError(f"'{column['name']}'invalid type"
                                             f" in item # {pos}")
                    values.append(value)
                rows.append(values)

        # CSV input data
        elif flask.request.content_type == constants.CSV_MIMETYPE:
            csvfile = io.BytesIO(flask.request.data)
            rows = dbshare.table.get_csv_rows(schema, csvfile, ',', True)

        # Unrecognized input data type
        else:
            flask.abort(http.client.UNSUPPORTED_MEDIA_TYPE)

        dbshare.table.insert_rows(db, schema, rows)
    except (ValueError, sqlite3.Error) as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for('api_table.table', dbname=dbname, tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/update', methods=['POST'])
def update(dbname, tablename):
    "POST: Update table rows in the table from CSV data; JSON not implemented."
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

    try:
        # CSV input data
        if flask.request.content_type == constants.CSV_MIMETYPE:
            csvfile = io.BytesIO(flask.request.data)
            dbshare.table.update_csv_rows(db, schema, csvfile, ',')

        # Unrecognized input data type
        else:
            flask.abort(http.client.UNSUPPORTED_MEDIA_TYPE)
    except (ValueError, sqlite3.Error) as error:
        utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for('api_table.table', dbname=dbname, tablename=tablename))

@blueprint.route('/<name:dbname>/<name:tablename>/empty', methods=['POST'])
def empty(dbname, tablename):
    "POST: Empty the table; delete all rows."
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
    try:
        with dbshare.db.DbContext(db) as ctx:
            ctx.empty_table(schema)
    except sqlite3.Error as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
    return flask.redirect(
        flask.url_for('api_table.table', dbname=dbname,tablename=tablename))

def get_json(db, table, complete=False):
    "Return JSON for the table."
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
