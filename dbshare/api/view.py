"View API endpoints."

import http.client

import flask

import dbshare.db
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint('api_view', __name__)

@blueprint.route('/<name:dbname>/<name:viewname>')
def view(dbname, viewname):
    "The schema for the view."
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
    result = get_api(db, schema, complete=True)
    result.update(schema)
    return flask.jsonify(utils.get_api(**result))

def get_api(db, view, complete=False):
    "Return the API JSON for the view."
    url = utils.url_for('view.rows',
                        dbname=db['name'],
                        viewname=view['name'])
    result = {'name': view['name'],
              'title': view.get('title'),
              'database': {'href': utils.url_for('api_db.database',
                                                 dbname=db['name'])},
              'nrows': view.get('nrows'),
              'rows': {'href': url + '.json'},
              'data': {'href': url + '.csv', 
                       'content_type': constants.CSV_MIMETYPE,
                       'format': 'csv'}
    }
    if complete:
        visuals = []
        for visual in db['visuals'].get(view['name'], []):
            url = utils.url_for('visual.display',
                                dbname=db['name'],
                                visualname=visual['name'])
            visuals.append({
                'name': visual['name'],
                'title': visual.get('title'),
                'specification': {'href': url + '.json'}})
        result['visualizations'] = visuals
    else:
        result['href'] = utils.url_for('api_view.view',
                                       dbname=db['name'],
                                       viewname=view['name'])
    return result
