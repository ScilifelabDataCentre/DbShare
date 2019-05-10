"Template API endpoints."

import flask

import dbportal.template
import dbportal.api_user

from dbportal import utils


blueprint = flask.Blueprint('api_template', __name__)

@blueprint.route('/<name:templatename>')
def template(templatename):
    "Display the template definition."
    try:
        template = dbportal.template.get_check_read(str(templatename))
    except ValueError as error:
        flask.abort(404)
    template['owner'] = dbportal.api_user.get_api_user(template['owner'])
    return flask.jsonify(utils.get_api(**template))
