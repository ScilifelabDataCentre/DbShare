"Template lists API endpoints."

import flask

import dbportal.templates

import dbportal.api_template
import dbportal.api_user

from dbportal import utils


blueprint = flask.Blueprint('api_templates', __name__)

@blueprint.route('/public')
def public():
    "Return the list of public templates."
    templates = dbportal.templates.get_templates(public=True)
    result = utils.get_api(title='Public templates',
                           templates=get_api(templates),
                           display={'href':
                                    utils.url_for('api_templates.public'),
                                    'format': 'html'})
    return flask.jsonify(result)

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Return the list of public templates."
    templates = dbportal.templates.get_templates()
    result = utils.get_api(title='All templates',
                           templates=get_api(templates),
                           display={'href': utils.url_for('templates.all'),
                                    'format': 'html'})
    return flask.jsonify(result)

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Return the list of templates owned by the given user."
    if not dbportal.templates.has_access(username):
        return flask.abort(401)
    templates = dbportal.templates.get_templates(owner=username)
    result = utils.get_api(title=f"Templates owned by {username}",
                           user=dbportal.api_user.get_api(username),
                           templates=get_api(templates),
                           display={'href': utils.url_for('templates.owner',
                                                          username=username),
                                    'format': 'html'})
    return flask.jsonify(result)

def get_api(templates, complete=False):
    "Return API JSON for the templates."
    result = {}
    for template in templates:
        data = dbportal.api_template.get_api(template, complete=complete)
        data['href'] = utils.url_for('api_template.template', 
                                     templatename=template['name'])
        result[template['name']] = data
    return result
