"View API endpoints."

import http.client

import flask

import dbshare.db

from dbshare import utils


blueprint = flask.Blueprint('api_view', __name__)

@blueprint.route('/<name:dbname>/<name:viewname>')
def view(dbname, tablename):
    "The definition for the view."
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
    result = schema.copy()
    result.update(get_api(db, schema))
    return flask.jsonify(utils.get_api(**result))

def get_api(db, view):
    "Return the API JSON for the view."
    result = {'name': view['name'],
              'title': view.get('title'),
              'api': {'href': utils.url_for('api_view.view',
                                            dbname=db['name'],
                                            viewname=view['name'])}
    }
    visuals = []
    for visual in db['visuals'].get(view['name'], []):
        url = utils.url_for('visual.display',
                            dbname=db['name'],
                            visualname=visual['name'])
        visuals.append({
            'title': visual.get('title'),
            'specification': {'href': url + '.json'},
            'display': {'href': url, 'format': 'html'}})
    url = utils.url_for('view.rows',
                        dbname=db['name'],
                        viewname=view['name'])
    result.update({
        'nrows': view['nrows'],
        'rows': {'href': url + '.json'},
        'data': {'href': url + '.csv', 'format': 'csv'},
        'display': {'href': url, 'format': 'html'},
        'visualizations': visuals})
    return result
