"Viztemplate lists endpoints."

import json

import flask

import dbportal.template
import dbportal.user
from dbportal import utils


blueprint = flask.Blueprint('templates', __name__)

@blueprint.route('/public')
def public():
    "Display the list of public viztemplates."
    templates = dbportal.template.get_templates(public=True)
    return flask.render_template('templates/public.html', templates=templates)

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Display the list of public viztemplates."
    return flask.render_template('templates/all.html',
                                 templates=dbportal.template.get_templates())

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Display the list of viztemplates owned by the given user."
    if not (flask.g.is_admin or flask.g.current_user['username'] == username):
        flask.flash("you may not access the list of the user's templates")
        return flask.redirect(flask.url_for('home'))
    return flask.render_template(
        'templates/owner.html',
        templates=dbportal.template.get_templates(owner=username),
        username=username)

@blueprint.route('/', methods=['GET', 'POST'])
@dbportal.user.login_required
def upload():
    "Upload a viztemplate from JSON."
    if utils.http_GET():
        return flask.render_template('templates/upload.html')

    elif utils.http_POST():
        try:
            templatefile = flask.request.files['templatefile']
            data = json.loads(templatefile.read().decode('utf-8'))
            with dbportal.template.TemplateContext() as ctx:
                ctx.set_name(flask.request.form.get('templatename') or
                             data['name'])
                ctx.set_title(data.get('title'))
                ctx.set_type(data['type'])
                ctx.template['fields'].update(data['fields'])
                ctx.set_code(data['code'])
        except (TypeError, ValueError, KeyError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.upload'))
        return flask.redirect(flask.url_for('template.view',
                                            templatename=ctx.template['name']))
