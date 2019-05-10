"Template lists HTML endpoints."

import json

import flask

import dbportal.template
import dbportal.user

from dbportal import utils


blueprint = flask.Blueprint('templates', __name__)

@blueprint.route('/public')
def public():
    "Display the list of public templates."
    return flask.render_template('templates/public.html',
                                 templates=get_templates(public=True))

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Display the list of public templates."
    return flask.render_template('templates/all.html',
                                 templates=get_templates())

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Display the list of templates owned by the given user."
    if not has_access(username):
        flask.flash("you may not access the list of the user's templates")
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('templates/owner.html',
                                 templates=get_templates(owner=username),
                                 username=username)

@blueprint.route('/', methods=['GET', 'POST'])
@dbportal.user.login_required
def upload():
    "Upload a template from JSON."
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
        return flask.redirect(flask.url_for('template.display',
                                            templatename=ctx.template['name']))

def has_access(username):
    "May the current user access the user's list of templates?"
    return flask.g.is_admin or flask.g.current_user['username'] == username

def get_templates(public=None, owner=None):
    "Get the list of templates according to criteria."
    sql = "SELECT name FROM templates"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' OR '.join(criteria.keys())
    sql += ' ORDER BY name'
    cursor = dbportal.system.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [dbportal.template.get_template(row[0]) for row in cursor]
