"Table API endpoints."

import flask

import dbportal.db

blueprint = flask.Blueprint('api_table', __name__)

@blueprint.route('/<name:dbname>/<name:tablename>')
def table(dbname, tablename):
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

def get_api_table(db, table, reduced=False):
    "Return the API JSON for the table."
    if reduced:
        result = {'database': {'href': utils.url_for('api_db.api_home',
                                                     dbname=db['name'])}
        }
    else:
        result = {'name': table['name'],
                  'title': table.get('title'),
                  'api': {'href': utils.url_for('api_table.table',
                                                dbname=db['name'],
                                                tablename=table['name'])}
        }
    visuals = {}
    for visual in db['visuals'].get(table['name'], []):
        url = utils.url_for('visual.display',
                            dbname=db['name'],
                            visualname=visual['name'])
        visuals[visual['name']] = {
            'title': visual.get('title'),
            'specification': {'href': url + '.json'},
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
