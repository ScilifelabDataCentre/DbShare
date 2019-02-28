"""User blueprint; user profile and login/logout.
This module must access an interface to a user database.
A module containing a UserDb class that is a subclass of userdb.BaseUserDb
must be defined at run time in the config variable USERDB_MODULE.
"""

import functools
import importlib
import urllib.parse

import flask
import flask_mail
import werkzeug.security

from . import constants
from . import utils

# User database interface module
userdb = None

def init_app(app):
    "Import the configured user database implementation and initialize it."
    global userdb
    userdb = importlib.import_module(app.config['USERDB_MODULE'])
    userdb.UserDb(app.config).initialize()

def get_current_user():
    "Return the current user for the session."
    db = userdb.UserDb(flask.current_app.config)
    try:
        try:
            return db[flask.session['username']]
        except KeyError:
            pass                # XXX Try API key
        else:
            if flask.session['expires'] <= utils.get_time():
                flask.session.pop('username', None)
                raise KeyError
    except KeyError:
        pass
    return None

def login_required(f):
    "Decorator for checking if logged in. Send to login page if not."
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.current_user:
            url = flask.url_for('.login')
            query = urllib.parse.urlencode({'next': flask.request.base_url})
            url += '?' + query
            return flask.redirect(url)
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    """Decorator for checking if logged in and 'admin' role.
    Otherwise status 403 Forbidden.
    """
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.is_admin:
            flask.abort(403)
        return f(*args, **kwargs)
    return wrap


blueprint = flask.Blueprint('user', __name__)

@blueprint.route('/login', methods=["GET", "POST"])
def login():
    "Login to a user account."
    if utils.is_method_GET():
        return flask.render_template('user/login.html')
    if utils.is_method_POST():
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        try:
            if username and password:
                do_login(username, password)
            else:
                raise ValueError
            try:
                next = urllib.parse.urlsplit(flask.request.form['next'])
            except KeyError:
                return flask.redirect(flask.url_for('index'))
            else:
                next = urllib.parse.urljoin(flask.request.host_url, next.path)
                return flask.redirect(next)
        except ValueError:
            flask.flash('invalid user or password', 'error')
            return flask.redirect(flask.url_for('.login'))

def do_login(username, password, db=None):
    "Set the session cookie if successful login."
    if db is None:
        db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[username]
    except KeyError:
        raise ValueError
    if not werkzeug.security.check_password_hash(user['password'],
                                                 password):
        raise ValueError
    flask.session['username'] = user['username']
    flask.session.permanent = True

@blueprint.route('/logout', methods=["POST"])
def logout():
    "Logout from the user account."
    del flask.session['username']
    return flask.redirect(flask.url_for('index'))

@blueprint.route('/register', methods=["GET", "POST"])
def register():
    "Register a new user account."
    if utils.is_method_GET():
        return flask.render_template('user/register.html')
    elif utils.is_method_POST():
        config = flask.current_app.config
        db = userdb.UserDb(config)
        try:
            user = db.create(flask.request.form.get('username'),
                             flask.request.form.get('email'),
                             role=constants.USER)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.register'))
        # Directly enabled; send code to the user.
        if user['status'] == constants.ENABLED:
            message = flask_mail.Message(
                "{} user account registration".format(config['SITE_NAME']),
                recipients=[user['email']])
            query = dict(username=user['username'],
                         code=user['password'][len('code:'):])
            message.body = "To set your password, go to {}".format(
                utils.get_absolute_url('.password', query=query))
            utils.mail.send(message)
            flask.flash('User account created; check your email.')
        # Set to 'pending'; send email to admins.
        else:
            message = flask_mail.Message(
                "{} user account pending".format(config['SITE_NAME']),
                recipients=db.get_admins_email())
            message.body = "To enable the user account, go to {}".format(
                utils.get_absolute_url('.account',
                                       values={'identifier': user['username']}))
            utils.mail.send(message)
            flask.flash('User account created; email will be sent when it'
                        ' has been enabled by the admin.')
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/password', methods=["GET", "POST"])
def password():
    "Set the password for a user account, and login user."
    if utils.is_method_GET():
        return flask.render_template('user/password.html',
                                     username=flask.request.args.get('username'),
                                     code=flask.request.args.get('code'))
    elif utils.is_method_POST():
        db = userdb.UserDb(flask.current_app.config)
        try:
            username = flask.request.form['username']
            user = db[username]
            code = flask.request.form['code']
            if user['password'] != "code:{}".format(code):
                raise KeyError
            password = flask.request.form.get('password') or ''
            if len(password) < flask.current_app.config['MIN_PASSWORD_LENGTH']:
                raise ValueError
        except KeyError:
            flask.flash('no such user or wrong code', 'error')
        except ValueError:
            flask.flash('too short password', 'error')
        else:
            db.set_password(user, password)
            do_login(username, password, db=db)
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/account/<id:identifier>')
@login_required
def account(identifier):
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[identifier]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    if not (flask.g.is_admin or 
            (flask.g.current_user and
             flask.g.current_user['username'] == user['username'])):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('user/account.html', user=user)

@blueprint.route('/account/<id:identifier>/enable', methods=["POST"])
@login_required
def enable(identifier):
    if not flask.g.is_admin:
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[identifier]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    db.set_status(user, constants.ENABLED)
    return flask.redirect(flask.url_for('.account', identifier=identifier))

@blueprint.route('/account/<id:identifier>/disable', methods=["POST"])
@login_required
def disable(identifier):
    if not flask.g.is_admin:
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[identifier]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    db.set_status(user, constants.DISABLED)
    return flask.redirect(flask.url_for('.account', identifier=identifier))
