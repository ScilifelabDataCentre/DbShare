"Template lists API endpoints."

import http.client

import flask

import dbshare.templates

import dbshare.api.template
import dbshare.api.user

from .. import utils


blueprint = flask.Blueprint('api_templates', __name__)

@blueprint.route('/public')
def public():
    "Return the list of public templates."
    result = {
        'title': 'Public templates',
        'templates': get_json(dbshare.templates.get_templates(public=True))
    }
    return utils.jsonify(utils.get_json(**result))

@blueprint.route('/all')
@dbshare.user.admin_required
def all():
    "Return the list of public templates."
    result = {
        'title': 'All templates',
        'templates': get_json(dbshare.templates.get_templates())
    }
    return utils.jsonify(utils.get_json(**result))

@blueprint.route('/owner/<name:username>')
@dbshare.user.login_required
def owner(username):
    "Return the list of templates owned by the given user."
    if not dbshare.templates.has_access(username):
        return flask.abort(http.client.UNAUTHORIZED)
    result = {
        'title': f"Templates owned by {username}",
        'user': dbshare.api.user.get_json(username),
        'templates': get_json(dbshare.templates.get_templates(owner=username))
    }
    return utils.jsonify(utils.get_json(**result))

def get_json(templates, complete=False):
    "Return JSON for the templates."
    result = {}
    for template in templates:
        data = dbshare.api.template.get_json(template, complete=complete)
        data['href'] = utils.url_for('api_template.template', 
                                     templatename=template['name'])
        result[template['name']] = data
    return result
