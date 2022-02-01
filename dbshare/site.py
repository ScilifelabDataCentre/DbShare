"Site HTML endpoints."

import http.client
import os.path

import flask


blueprint = flask.Blueprint('site', __name__)

@blueprint.route('/static/<filename>')
def static(filename):
    "Static file for the site."
    path = flask.current_app.config['SITE_STATIC_DIR']
    path = os.path.expandvars(os.path.expanduser(path))
    if path:
        return flask.send_from_directory(path, filename)
    else:
        flask.abort(http.client.NOT_FOUND)
