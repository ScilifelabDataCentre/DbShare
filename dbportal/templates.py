"Vis-template lists endpoints."

import flask

import dbportal.template
import dbportal.user

blueprint = flask.Blueprint('templates', __name__)

@blueprint.route('/public')
def public():
    "Display the list of public vis-templates."
    templates = dbportal.template.get_templates(public=True)
    return flask.render_template('templates/public.html', templates=templates)

@blueprint.route('/all')
@dbportal.user.login_required
@dbportal.user.admin_required
def all():
    "Display the list of public vis-templates."
    return flask.render_template('templates/all.html',
                                 templates=dbportal.template.get_templates())

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Display the list of vis-templates owned by the given user."
    if not (flask.g.is_admin or flask.g.current_user['username'] == username):
        flask.flash("you may not access the list of the user's templates")
        return flask.redirect(flask.url_for('home'))
    return flask.render_template(
        'templates/owner.html',
        templates=dbportal.template.get_templates(owner=username),
        username=username)
