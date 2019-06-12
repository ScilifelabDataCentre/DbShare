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
    return flask.jsonify(
        utils.get_json(title='Public templates',
                       templates=get_json(
                           dbshare.templates.get_templates(public=True))))

@blueprint.route('/all')
@dbshare.user.admin_required
def all():
    "Return the list of public templates."
    return flask.jsonify(
        utils.get_json(title='All templates',
                       templates=get_json(dbshare.templates.get_templates())))

@blueprint.route('/owner/<name:username>')
@dbshare.user.login_required
def owner(username):
    "Return the list of templates owned by the given user."
    if not dbshare.templates.has_access(username):
        return flask.abort(http.client.UNAUTHORIZED)
    return flask.jsonify(
        utils.get_json(title=f"Templates owned by {username}",
                       user=dbshare.api.user.get_json(username),
                       templates=get_json(
                           dbshare.templates.get_templates(owner=username))))

def get_json(templates, complete=False):
    "Return JSON for the templates."
    result = {}
    for template in templates:
        data = dbshare.api.template.get_json(template, complete=complete)
        data['href'] = utils.url_for('api_template.template', 
                                     templatename=template['name'])
        result[template['name']] = data
    return result
