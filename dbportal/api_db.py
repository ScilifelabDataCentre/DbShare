"Database API endpoints."

import flask

import dbportal.db

from dbportal import utils

blueprint = flask.Blueprint('api_db', __name__)

@blueprint.route('/<name:dbname>', methods=['GET', 'POST', 'DELETE'])
def database(dbname):
    "List the database tables, views and metadata. Delete the database."
    if utils.http_GET():
        try:
            db = dbportal.db.get_check_read(str(dbname), nrows=True)
        except ValueError as error:
            flask.abort(404, message=str(error))
        return flask.jsonify(utils.get_api(**get_api(db, complete=True)))
 
    elif utils.http_POST():
        raise NotImplementedError
 
    elif utils.http_DELETE():
        raise NotImplementedError

def get_api(db, complete=False):
    "Return the API for the database."
    result = {'name': db['name'],
              'title': db.get('title'),
              'owner': dbportal.user.get_api(db['owner']),
              'public': db['public'],
              'readonly': db['readonly'],
              'size': db['size'],
              'modified': db['modified'],
              'created': db['created']}
    if complete:
        result['tables'] = {}
        for tablename, table in db['tables'].items():
            result['tables'][tablename] = \
                dbportal.api_table.get_api_table(db, table)
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
                                                   dbname=db['name'])}
    return result
