"Template API endpoints."

import http.client

import flask

import dbshare.template
import dbshare.api.user

from .. import utils


blueprint = flask.Blueprint('api_template', __name__)

@blueprint.route('/<name:templatename>')
def template(templatename):
    "Return the API JSON for the template."
    try:
        template = dbshare.template.get_check_read(str(templatename))
    except ValueError:
        flask.abort(http.client.UNAUTHORIZED)
    except KeyError:
        flask.abort(http.client.NOT_FOUND)
    return flask.jsonify(utils.get_json(**get_json(template)))

def get_json(template, complete=False):
    "Return JSON for the template."
    if complete:
        result = template.copy()
        result['owner'] = dbshare.api_user.get_json(template['owner'])
    else:
        result = {'name': template['name'],
                  'owner': dbshare.api_user.get_json(template['owner']),
                  'public': template['public'],
                  'modified': template['modified'],
                  'created': template['created']}
    return result
