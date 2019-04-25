"Database lists endpoints."

import flask

import dbportal.db
import dbportal.user

blueprint = flask.Blueprint('dbs', __name__)

@blueprint.route('/public')
def public():
    "Display the list of public databases."
    return flask.render_template('dbs/public.html',
                                 dbs=dbportal.db.get_dbs(public=True))

@blueprint.route('/all')
@dbportal.user.login_required
@dbportal.user.admin_required
def all():
    "Display the list of all databases."
    dbs = dbportal.db.get_dbs()
    return flask.render_template('dbs/all.html',
                                 dbs=dbs,
                                 usage=sum([db['size'] for db in dbs]))

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Display the list of databases owned by the given user."
    if not (flask.g.is_admin or flask.g.current_user['username'] == username):
        flask.flash("you may not access the list of the user's databases")
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('dbs/owner.html',
                                 dbs=dbportal.db.get_dbs(owner=username),
                                 username=username)
