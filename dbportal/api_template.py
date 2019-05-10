"Template API endpoints."

import flask

import dbportal.template
import dbportal.api_user

from dbportal import utils


blueprint = flask.Blueprint('api_template', __name__)

@blueprint.route('/<name:templatename>')
def template(templatename):
    "Return the API JSON for the template."
    try:
        template = dbportal.template.get_check_read(str(templatename))
    except ValueError as error:
        flask.abort(404)
    return flask.jsonify(utils.get_api(**get_api(template)))

def get_api(template):
    "Return the JSON for the template."
    result = template.copy()
    result['owner'] = dbportal.api_user.get_api(template['owner'])
    return result
