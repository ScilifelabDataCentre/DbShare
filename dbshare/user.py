"User profile and login/logout HTMl endpoints."

import functools
import http.client
import json
import re
import sqlite3

import flask
import flask_mail
import werkzeug.security

import dbshare.system

from dbshare import constants
from dbshare import utils


def login_required(f):
    "Decorator for checking if logged in. Send to login page if not."
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.current_user:
            url = flask.url_for('user.login', next=flask.request.base_url)
            return flask.redirect(url)
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    """Decorator for checking if logged in and 'admin' role.
    Otherwise return status 401 Unauthorized.
    """
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.is_admin:
            flask.abort(http.client.UNAUTHORIZED)
        return f(*args, **kwargs)
    return wrap


blueprint = flask.Blueprint('user', __name__)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    "Login to a user account."
    if utils.http_GET():
        return flask.render_template('user/login.html',
                                     next=flask.request.args.get('next'))
    if utils.http_POST():
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        try:
            if username and password:
                do_login(username, password)
            else:
                raise ValueError
            try:
                next = flask.request.form['next']
            except KeyError:
                return flask.redirect(flask.url_for('home'))
            else:
                return flask.redirect(next)
        except ValueError:
            flask.flash('invalid user/password, or account disabled', 'error')
            return flask.redirect(flask.url_for('.login'))

def do_login(username, password):
    """Set the session cookie if successful login.
    Raise ValueError if some problem.
    """
    user = get_user(username)
    if user is None: raise ValueError
    if not werkzeug.security.check_password_hash(user['password'], password):
        raise ValueError
    if user['status'] != constants.ENABLED:
        raise ValueError
    flask.session['username'] = user['username']
    flask.session.permanent = True

@blueprint.route('/logout', methods=['POST'])
def logout():
    "Logout from the user account."
    del flask.session['username']
    return flask.redirect(flask.url_for('home'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    "Register a new user account."
    if utils.http_GET():
        return flask.render_template('user/register.html')

    elif utils.http_POST():
        try:
            with UserContext() as ctx:
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
            cnx = dbshare.system.get_cnx()
            sql = "SELECT email FROM users WHERE role=?"
            cursor = cnx.execute(sql, (constants.ADMIN,))
            emails = [row[0] for row in cursor]
            site = flask.current_app.config['SITE_NAME']
            message = flask_mail.Message(f"{site} user account pending",
                                         recipients=emails)
            url = utils.url_for('.profile', username=user['username'])
            message.body = f"To enable the user account, go to {url}"
            utils.mail.send(message)
            flask.flash('User account created; an email will be sent when'
                        ' it has been enabled by the admin.')
        return flask.redirect(flask.url_for('home'))

@blueprint.route('/reset', methods=['GET', 'POST'])
def reset():
    "Reset the password for a user account and send email."
    if utils.http_GET():
        return flask.render_template('user/reset.html')

    elif utils.http_POST():
        try:
            user = get_user(email=flask.request.form['email'])
            if user is None: raise KeyError
            if user['status'] != constants.ENABLED: raise KeyError
        except KeyError:
            pass
        else:
            with UserContext(user) as ctx:
                ctx.set_password()
            send_password_code(user, 'password reset')
        flask.flash('An email has been sent if the user account exists.')
        return flask.redirect(flask.url_for('home'))

def send_password_code(user, action):
    "Send an email with the one-time code to the user's email address."
    site = flask.current_app.config['SITE_NAME']
    message = flask_mail.Message(f"{site} user account {action}",
                                 recipients=[user['email']])
    url = utils.url_for('.password',
                        username=user['username'],
                        code=user['password'][len('code:'):])
    message.body = f"To set your password, go to {url}"
    utils.mail.send(message)

@blueprint.route('/password', methods=['GET', 'POST'])
def password():
    "Set the password for a user account, and login user."
    if utils.http_GET():
        return flask.render_template(
            'user/password.html',
            username=flask.request.args.get('username'),
            code=flask.request.args.get('code'))

    elif utils.http_POST():
        try:
            username = flask.request.form['username']
            if not username: raise KeyError
            user = get_user(username=username)
            if user is None: raise KeyError
            if user['password'] != "code:{}".format(flask.request.form['code']):
                raise KeyError
            password = flask.request.form.get('password') or ''
            if len(password) < flask.current_app.config['MIN_PASSWORD_LENGTH']:
                raise ValueError
        except KeyError:
            flask.flash('no such user or wrong code', 'error')
        except ValueError:
            flask.flash('too short password', 'error')
        else:
            with UserContext(user) as ctx:
                ctx.set_password(password)
            do_login(username, password)
        return flask.redirect(flask.url_for('home'))

@blueprint.route('/profile/<name:username>')
@login_required
def profile(username):
    "Display the profile of the given user."
    import dbshare.template
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('home'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('home'))
    ndbs, usage = dbshare.db.get_usage(username)
    ntemplates = len(dbshare.templates.get_templates(owner=username))
    deletable = ndbs == 0 and ntemplates == 0
    return flask.render_template('user/profile.html',
                                 user=user,
                                 enable_disable=is_admin_and_not_self(user),
                                 ndbs=ndbs,
                                 usage=usage,
                                 ntemplates=ntemplates,
                                 deletable=deletable)

@blueprint.route('/profile/<name:username>/edit',
                 methods=['GET', 'POST', 'DELETE'])
@login_required
def edit(username):
    "Edit the user profile. Or delete the user."
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('home'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('user/edit.html',
                                     user=user,
                                     change_role=is_admin_and_not_self(user))

    elif utils.http_POST():
        with UserContext(user) as ctx:
            email = flask.request.form.get('email')
            if email != user['email']:
                ctx.set_email(enail)
            if is_admin_and_not_self(user):
                ctx.set_role(flask.request.form.get('role'))
            if flask.request.form.get('apikey'):
                ctx.set_apikey()
            quota = flask.request.form.get('quota') or None
            if quota:
                try:
                    quota = int(quota)
                except (ValueError, TypeError):
                    quota = -1
            ctx.set_quota(quota)
        return flask.redirect(
            flask.url_for('.profile', username=user['username']))

    elif utils.http_DELETE():
        if not (ndbs == 0 and ntemplates == 0):
            flash.flash('cannot delete non-empty user account', 'error')
            return flask.redirect(flask.url_for('.profile', username=username))
        cnx = dbshare.system.get_cnx(write=True)
        with cnx:
            sql = "DELETE FROM users_logs WHERE username=?"
            cnx.execute(sql, (username,))
            sql = "DELETE FROM users WHERE username=?"
            cnx.execute(sql, (username,))
        flask.flash(f"Deleted user {username}.", 'message')
        if flask.g.is_admin:
            return flask.redirect(flask.url_for('.users'))
        else:
            return flask.redirect(flask.url_for('home'))

@blueprint.route('/profile/<name:username>/logs')
@login_required
def logs(username):
    "Display the log records of the given user."
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('home'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('home'))
    cursor = dbshare.system.get_cursor()
    sql = "SELECT new, editor, remote_addr, user_agent, timestamp" \
          " FROM users_logs WHERE username=? ORDER BY timestamp DESC"
    cursor.execute(sql, (user['username'],))
    logs = [{'new': json.loads(row[0]),
             'editor': row[1],
             'remote_addr': row[2],
             'user_agent': row[3],
             'timestamp': row[4]}
            for row in cursor]
    return flask.render_template('user/logs.html', user=user, logs=logs)

@blueprint.route('/users')
@admin_required
def users():
    "Display list of all users."
    import dbshare.dbs
    import dbshare.templates
    cursor = dbshare.system.get_cursor()
    sql = "SELECT username, email, password, apikey," \
          " role, status, quota, created, modified FROM users"
    cursor.execute(sql)
    users = [{'username':   row[0],
              'email':      row[1],
              'password':   row[2],
              'apikey':     row[3],
              'role':       row[4],
              'status':     row[5],
              'quota':      row[6],
              'created':    row[7],
              'modified':   row[8],
              'ndbs':       0,
              'size':       0,
              'ntemplates': len(dbshare.templates.get_templates(owner=row[0]))}
             for row in cursor]
    lookup = dict([(u['username'], u) for u in users])
    for db in dbshare.dbs.get_dbs():
        lookup[db['owner']]['ndbs'] += 1
        lookup[db['owner']]['size'] += db['size']
    return flask.render_template('user/users.html', users=users)

@blueprint.route('/enable/<name:username>', methods=['POST'])
@admin_required
def enable(username):
    "Enable the given user account."
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('home'))
    with UserContext(user) as ctx:
        ctx.set_status(constants.ENABLED)
        ctx.set_password()
    send_password_code(user, 'enabled')
    return flask.redirect(flask.url_for('.profile', username=username))

@blueprint.route('/disable/<name:username>', methods=['POST'])
@admin_required
def disable(username):
    "Disable the given user account."
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('home'))
    with UserContext(user) as ctx:
        ctx.set_status(constants.DISABLED)
    return flask.redirect(flask.url_for('.profile', username=username))


class UserContext:
    "Context for creating, modifying and saving a user account."

    def __init__(self, user=None):
        if user is None:
            if flask.current_app.config['USER_ENABLE_IMMEDIATELY']:
                status = constants.ENABLED
            else:
                status = constants.PENDING
            self.user = {'status': status, 
                         'quota':flask.current_app.config['USER_DEFAULT_QUOTA'],
                         'created': utils.get_time()}
            self.orig = {}
        else:
            self.user = user
            self.orig = user.copy()
        self.cnx = dbshare.system.get_cnx(write=True)

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['username', 'email', 'role', 'status']:
            if not self.user.get(key):
                raise ValueError("invalid user: %s not set" % key)
        self.user['modified'] = utils.get_time()
        cursor = self.cnx.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username=?",
                       (self.user['username'],))
        rows = cursor.fetchall()
        with self.cnx:
            # Update user
            if rows[0][0]:
                sql = "UPDATE users SET email=?, password=?," \
                      " apikey=?, role=?, status=?, quota=?, modified=?" \
                      " WHERE username=?"
                self.cnx.execute(sql, (self.user['email'],
                                       self.user['password'],
                                       self.user.get('apikey'),
                                       self.user['role'],
                                       self.user['status'],
                                       self.user['quota'],
                                       self.user['modified'],
                                       self.user['username']))
            # Add user
            else:
                sql = "INSERT INTO users" \
                      " (username, email, password, apikey, role," \
                      "  status, quota, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.cnx.execute(sql, (self.user['username'],
                                       self.user['email'],
                                       self.user['password'],
                                       self.user.get('apikey'),
                                       self.user['role'],
                                       self.user['status'],
                                       self.user['quota'],
                                       self.user['created'], 
                                       self.user['modified']))
            # Add log entry
            new = {}
            for key, value in self.user.items():
                if value != self.orig.get(key):
                    new[key] = value
            new.pop('modified')
            try:
                password = new['password']
            except KeyError:
                pass
            else:
                if not password.startswith('code:'):
                    new['password'] = '***'
            try:
                if flask.g.current_user:
                    editor = flask.g.current_user['username']
                else:
                    editor = None
            except AttributeError:
                editor = None
            if flask.has_request_context():
                remote_addr = str(flask.request.remote_addr)
                user_agent = str(flask.request.user_agent)
            else:
                remote_addr = None
                user_agent = None
            sql = "INSERT INTO users_logs (username, new, editor," \
                  " remote_addr, user_agent, timestamp)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
            self.cnx.execute(sql, (self.user['username'],
                                  json.dumps(new, ensure_ascii=False),
                                  editor,
                                  remote_addr,
                                  user_agent,
                                  utils.get_time()))

    def set_username(self, username):
        if 'username' in self.user:
            raise ValueError('username cannot be changed')
        if not constants.NAME_RX.match(username):
            raise ValueError('invalid username; must be an name')
        if get_user(username=username, cnx=self.cnx):
            raise ValueError('username already in use')
        self.user['username'] = username

    def set_email(self, email):
        if not constants.EMAIL_RX.match(email):
            raise ValueError('invalid email')
        if get_user(email=email, cnx=self.cnx):
            raise ValueError('email already in use')
        self.user['email'] = email
        if self.user.get('status') == constants.PENDING:
            for rx in flask.current_app.config['USER_ENABLE_EMAIL_WHITELIST']:
                if re.match(rx, email):
                    self.set_status(constants.ENABLED)
                    break

    def set_status(self, status):
        if status not in constants.USER_STATUSES:
            raise ValueError('invalid status')
        self.user['status'] = status

    def set_quota(self, quota):
        if quota is not None and quota <= 0:
            quota = flask.current_app.config['USER_DEFAULT_QUOTA']
        self.user['quota'] = quota

    def set_role(self, role):
        if role not in constants.USER_ROLES:
            raise ValueError('invalid role')
        self.user['role'] = role

    def set_password(self, password=None):
        "Set the password; a one-time code if no password provided."
        config = flask.current_app.config
        if password is None:
            self.user['password'] = "code:%s" % utils.get_iuid()
        else:
            if len(password) < config['MIN_PASSWORD_LENGTH']:
                raise ValueError('password too short')
            self.user['password'] = werkzeug.security.generate_password_hash(
                password, salt_length=config['SALT_LENGTH'])

    def set_apikey(self):
        "Set a new API key."
        self.user['apikey'] = utils.get_iuid()


# Utility functions

def get_user(username=None, email=None, apikey=None, cnx=None):
    """Return the user for the given username, email or apikey.
    Return None if no such user.
    """
    if username:
        name      = username
        criterion = " WHERE username=?"
    elif email:
        name      = email
        criterion = " WHERE email=?"
    elif apikey:
        name      = apikey
        criterion = " WHERE apikey=?"
    else:
        return None
    if cnx is None:
        cursor = dbshare.system.get_cursor()
    else:
        cursor = cnx.cursor()
    sql = "SELECT username, email, password, apikey, role, status," \
          " quota, created, modified FROM users" + criterion
    cursor.execute(sql, (name,))
    rows = cursor.fetchall()
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    return {'username': row[0],
            'email':    row[1],
            'password': row[2],
            'apikey':   row[3],
            'role':     row[4],
            'status':   row[5],
            'quota':    row[6],
            'created':  row[7],
            'modified': row[8]}
    
def get_current_user():
    """Return the user for the current session.
    Return None if no such user, or disabled.
    """
    user = get_user(username=flask.session.get('username'),
                    apikey=flask.request.headers.get('x-apikey'))
    if user is None: return None
    if user['status'] == constants.ENABLED:
        return user
    else:
        flask.session.pop('username', None)
        return None

def is_admin_or_self(user):
    "Is the current user admin, or the same as the given user?"
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == user['username']

def is_admin_and_not_self(user):
    "Is the current user admin, but not the same as the given user?"
    if flask.g.is_admin:
        return flask.g.current_user['username'] != user['username']
    return False
