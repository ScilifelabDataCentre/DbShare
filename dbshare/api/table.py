"Table API endpoints."

import http.client

import flask

import dbshare.db
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
                ctx.add_table(data)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(flask.url_for('api_db.database', dbname=dbname))

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
