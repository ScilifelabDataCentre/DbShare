"Database API endpoints."

import http.client
import io

import flask

import dbshare.db

from dbshare import utils

blueprint = flask.Blueprint('api_db', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def database(dbname):
    """GET: List the database tables, views and metadata.
    PUT: Create a database.
    POST: Edit the database.
    DELETE: Delete the database.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname, nrows=True)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        return flask.jsonify(utils.get_api(**get_api(db, complete=True)))
 
    elif utils.http_PUT():
        try:
            dbshare.db.get_check_read(dbname)
        except ValueError:
            flask.abort(http.client.FORBIDDEN)
        except KeyError:
            pass
        else:
            flask.abort(http.client.FORBIDDEN)
        try:
            if flask.request.content_length:
                db = dbshare.db.add_database(
                    dbname,
                    infile=io.BytesIO(flask.request.get_data()),
                    size=flask.request.content_length)
            else:
                with dbshare.db.DbContext() as ctx:
                    ctx.set_name(dbname)
                    ctx.initialize()
                db = ctx.db
        except ValueError as error:
            print(str(error))
            flask.abort(http.client.BAD_REQUEST)
        return flask.redirect(flask.url_for('api_db.database', dbname=dbname))

    elif utils.http_POST():
        raise NotImplementedError
 
    elif utils.http_DELETE():
        try:
            dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        dbshare.db.delete_database(dbname)
        return ('', http.client.NO_CONTENT)

def get_api(db, complete=False):
    "Return the API for the database."
    result = {'name': db['name'],
              'title': db.get('title'),
              'owner': dbshare.api_user.get_api(db['owner']),
              'public': db['public'],
              'readonly': db['readonly'],
              'size': db['size'],
              'modified': db['modified'],
              'created': db['created']}
    if complete:
        result['tables'] = {}
        for tablename, table in db['tables'].items():
            result['tables'][tablename] = dbshare.api_table.get_api(db, table)
        result['views'] = {}
        for viewname, view in db['views'].items():
            visuals = {}
            for visual in db['visuals'].get(viewname, []):
                url = utils.url_for('visual.display',
                                    dbname=db['name'],
                                    visualname=visual['name'])
                visuals[visual['name']] = {
                    'title': visual.get('title'),
                    'spec': url + '.json',
                    'display': {'href': url, 'format': 'html'}}
            url = utils.url_for('view.rows',
                                dbname=db['name'],
                                viewname=viewname)
            result['views'][viewname] = {
                'title': view.get('title'),
                'nrows': view['nrows'],
                'rows': {'href': url + '.json'},
                'data': {'href': url + '.csv', 'format': 'csv'},
                'display': {'href': url, 'format': 'html'},
                'visualizations': visuals}
        result['display'] = {'href': utils.url_for('db.display',
                                                   dbname=db['name']),
                             'format': 'html'}
    return result
