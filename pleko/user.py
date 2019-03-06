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
        user = db[flask.session['username']]
    except KeyError:
        try:
            user = db[flask.request.headers['x-apikey']]
        except KeyError:
            return None
    if user['status'] == constants.ENABLED:
        return user
    else:
        flask.session.pop('username', None)
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
        return flask.render_template('user/login.html',
                                     next=flask.request.args.get('next'))
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
            flask.flash('invalid user or password, or disabled', 'error')
            return flask.redirect(flask.url_for('.login'))

def do_login(username, password, db=None):
    "Set the session cookie if successful login."
    if db is None:
        db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[username]
    except KeyError:
        raise ValueError
    if not werkzeug.security.check_password_hash(user['password'], password):
        raise ValueError
    if user['status'] != constants.ENABLED:
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
            with db.get_context() as ctx:
                ctx.set_username(flask.request.form.get('username'))
                ctx.set_email(flask.request.form.get('email'))
                ctx.set_role(constants.USER)
                ctx.set_password()
            user = ctx.user
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.register'))
        # Directly enabled; send code to the user.
        if user['status'] == constants.ENABLED:
            send_password_code(user, 'registration')
            flask.flash('User account created; check your email.')
        # Was set to 'pending'; send email to admins.
        else:
            message = flask_mail.Message(
                "{} user account pending".format(config['SITE_NAME']),
                recipients=db.get_admins_email())
            message.body = "To enable the user account, go to {}".format(
                utils.get_absolute_url('.account',
                                       values={'username': user['username']}))
            utils.mail.send(message)
            flask.flash('User account created; an email will be sent when'
                        ' it has been enabled by the admin.')
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/reset', methods=["GET", "POST"])
def reset():
    "Reset the password for a user account and send email."
    if utils.is_method_GET():
        return flask.render_template('user/reset.html')
    elif utils.is_method_POST():
        db = userdb.UserDb(flask.current_app.config)
        try:
            email = flask.request.form['email']
            user = db[email]
            if user['status'] != constants.ENABLED: raise KeyError
        except KeyError:
            pass
        else:
            with db.get_context(user) as ctx:
                ctx.set_password()
            send_password_code(user, 'password reset')
        flask.flash('An email has been sent if the user account exists.')
        return flask.redirect(flask.url_for('index'))

def send_password_code(user, action):
    "Send an email with the one-time code to the user's email address."
    message = flask_mail.Message(
        "{} user account {}".format(flask.current_app.config['SITE_NAME'],
                                    action),
        recipients=[user['email']])
    query = dict(username=user['username'],
                 code=user['password'][len('code:'):])
    message.body = "To set your password, go to {}".format(
        utils.get_absolute_url('.password', query=query))
    utils.mail.send(message)

@blueprint.route('/password', methods=["GET", "POST"])
def password():
    "Set the password for a user account, and login user."
    if utils.is_method_GET():
        return flask.render_template(
            'user/password.html',
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
            with db.get_context(user) as ctx:
                ctx.set_password(password)
            do_login(username, password, db=db)
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/account/<id:username>')
@login_required
def account(username):
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[username]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    enable_disable = flask.g.is_admin and flask.g.current_user != user
    return flask.render_template('user/account.html',
                                 user=user,
                                 enable_disable=enable_disable)

def is_admin_or_self(user):
    "Is the current user admin, or the same as the given user?"
    if flask.g.is_admin: return True
    if not flask.g.current_user: return False
    return flask.g.current_user['username'] == user['username']

def is_admin_and_not_self(user):
    "Is the current user admin, but not the same as the given user?"
    if flask.g.is_admin:
        return flask.g.current_user['username'] != user['username']
    return False

@blueprint.route('/edit/<id:username>', methods=["GET", "POST"])
@login_required
def edit(username):
    "Edit the user account."
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[username]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    if utils.is_method_GET():
        return flask.render_template('user/edit.html',
                                     user=user,
                                     is_admin_and_not_self=is_admin_and_not_self(user))
    elif utils.is_method_POST():
        with db.get_context(user) as ctx:
            email = flask.request.form.get('email')
            if email != user['email']:
                ctx.set_email(enail)
            if is_admin_and_not_self(user):
                ctx.set_role(flask.request.form.get('role'))
            if flask.request.form.get('apikey'):
                ctx.set_apikey()
        return flask.redirect(
            flask.url_for('.account', username=user['username']))

@blueprint.route('/accounts')
@login_required
def accounts():
    db = userdb.UserDb(flask.current_app.config)
    return flask.render_template('user/accounts.html', users=list(db))

@blueprint.route('/account/<id:username>/enable', methods=["POST"])
@login_required
def enable(username):
    if not flask.g.is_admin:
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[username]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    with db.get_context(user) as ctx:
        ctx.set_status(constants.ENABLED)
        ctx.set_password()
    send_password_code(user, 'enabled')
    return flask.redirect(flask.url_for('.account', username=username))

@blueprint.route('/account/<id:username>/disable', methods=["POST"])
@login_required
def disable(username):
    if not flask.g.is_admin:
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    db = userdb.UserDb(flask.current_app.config)
    try:
        user = db[username]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    with db.get_context(user) as ctx:
        ctx.set_status(constants.DISABLED)
    return flask.redirect(flask.url_for('.account', username=username))
