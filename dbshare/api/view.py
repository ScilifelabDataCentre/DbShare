"View API endpoints."

import http.client

import flask
import jsonschema

import dbshare.db

from .. import constants
from .. import utils


blueprint = flask.Blueprint('api_view', __name__)

@blueprint.route('/<name:dbname>/<name:viewname>',
                 methods=['GET', 'PUT', 'DELETE'])
def view(dbname, viewname):
    """GET: Return the schema for the view.
    PUT: Create the view.
    DELETE: Delete the view.
    """
    if utils.http_GET():
        try:
            db = dbshare.db.get_check_read(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            schema = db['views'][viewname]
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        result = get_json(db, schema, complete=True)
        result.update(schema)
        return utils.jsonify(utils.get_json(**result), schema='/view')

    elif utils.http_PUT():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbContext(db) as ctx:
                ctx.add_view(flask.request.get_json(), create=True)
        except (jsonschema.ValidationError, ValueError) as error:
            print(error)
            utils.abort_json(http.client.BAD_REQUEST, error)
        return flask.redirect(
            flask.url_for('api_view.view', dbname=dbname, viewname=viewname))

    elif utils.http_DELETE():
        try:
            db = dbshare.db.get_check_write(dbname)
        except ValueError:
            flask.abort(http.client.UNAUTHORIZED)
        except KeyError:
            flask.abort(http.client.NOT_FOUND)
        try:
            with dbshare.db.DbContext(db) as ctx:
                ctx.delete_view(viewname)
        except ValueError as error:
            utils.abort_json(http.client.BAD_REQUEST, error)
        return ('', http.client.NO_CONTENT)

def get_json(db, view, complete=False):
    "Return the JSON for the view."
    url = utils.url_for('view.rows',
                        dbname=db['name'],
                        viewname=view['name'])
    result = {'name': view['name'],
              'title': view.get('title'),
              'description': view.get('description'),
              'nrows': view.get('nrows'),
              'rows': {'href': url + '.json'},
              'data': {'href': url + '.csv', 
                       'content-type': constants.CSV_MIMETYPE,
                       'format': 'csv'}
    }
    if complete:
        result['database'] = {'href': utils.url_for('api_db.database',
                                                    dbname=db['name'])}
        # visuals = []
        # for visual in db['visuals'].get(view['name'], []):
        #     url = utils.url_for('visual.display',
        #                         dbname=db['name'],
        #                         visualname=visual['name'])
        #     visuals.append({
        #         'name': visual['name'],
        #         'title': visual.get('title'),
        #         'specification': {'href': url + '.json'}})
        # result['visualizations'] = visuals
    else:
        result['href'] = utils.url_for('api_view.view',
                                       dbname=db['name'],
                                       viewname=view['name'])
    return result
