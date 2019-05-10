"Template lists API endpoints."

import flask

import dbportal.api_template
import dbportal.templates

from dbportal import utils


blueprint = flask.Blueprint('api_templates', __name__)

@blueprint.route('/public')
def public():
    "Return the list of public templates."
    templates = dbportal.templates.get_templates(public=True)
    result = utils.get_api(title='Public templates',
                           templates=get_api(templates),
                           display={'href': utils.url_for('templates.public'),
                                    'format': 'html'})
    return flask.jsonify(results)

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Return the list of public templates."
    return flask.render_template('templates/all.html',
                                 templates=dbportal.template.get_templates())

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Return the list of templates owned by the given user."
    if not dbportal.templates.has_access(username):
        return flask.abort(401)
    templates = dbportal.template.get_templates(owner=username)
    result = utils.get_api(title='Public templates',
                           templates=get_api(templates),
                           display={'href': utils.url_for('templates.public'),
                                    'format': 'html'})
    return flask.jsonify(results)

def get_api(templates):
    "Return API JSON for the templates."
    result = {}
    for template in templates:
        data = dbportal.api_template.get_api(template)
        data['href'] = utils.url_for('api_template.template', 
                                     templatename=template['name'])
        result[template['name']] = data
    return result
