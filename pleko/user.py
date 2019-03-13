"User blueprint; user profile and login/logout."

import functools
import json
import re
import sqlite3
import urllib.parse

import flask
import flask_mail
import werkzeug.security

import pleko.constants
import pleko.utils


def init_app(app):
    "Initialize the users tables in the master Sqlite3 database, if not done."
    db = pleko.utils.get_masterdb(app)
    db.execute("CREATE TABLE IF NOT EXISTS users"
               "(username PRIMARY KEY,"
               " email TEXT NOT NULL UNIQUE,"
               " password TEXT,"
               " apikey TEXT,"
               " role TEXT NOT NULL,"
               " status TEXT NOT NULL,"
               " profile TEXT NOT NULL,"
               " created TEXT NOT NULL,"
               " modified TEXT NOT NULL)")
    db.execute("CREATE INDEX IF NOT EXISTS users_apikey_ix"
               " ON users (apikey)")
    db.execute("CREATE TABLE IF NOT EXISTS users_logs"
               "(username TEXT NOT NULL REFERENCES users (username),"
               " prev TEXT NOT NULL,"
               " editor TEXT,"
               " remote_addr TEXT,"
               " user_agent TEXT,"
               " timestamp TEXT NOT NULL)")
    db.execute("CREATE INDEX IF NOT EXISTS users_logs_username_ix"
               " ON users_logs (username)")

def get_user(username=None, email=None, apikey=None, db=None):
    """Return the user for the given username, email or apikey.
    Return None if no such user.
    """
    if username:
        identifier = username
        criterion = " WHERE username=?"
    elif email:
        identifier = email
        criterion = " WHERE email=?"
    elif apikey:
        identifier = apikey
        criterion = " WHERE apikey=?"
    else:
        raise ValueError('neither username, email nor apikey provided')
    if db is None:
        db = flask.g.db
    cursor = db.cursor()
    sql = "SELECT username, email, password, apikey," \
          " role, status, profile, created, modified FROM users" + criterion
    cursor.execute(sql, (identifier,))
    rows = list(cursor)
    if len(rows) == 1:
        row = rows[0]
        return {'username': row[0],
                'email':    row[1],
                'password': row[2],
                'apikey':   row[3],
                'role':     row[4],
                'status':   row[5],
                'profile':  json.loads(row[6]),
                'created':  row[7],
                'modified': row[8]}
    else:
        return None
    
def get_current_user():
    """Return the user for the current session.
    Return None if no such user, or disabled.
    """
    user = get_user(username=flask.session.get('username'),
                    apikey=flask.request.headers.get('x-apikey'))
    if user is None: return None
    if user['status'] == pleko.constants.ENABLED:
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
    if pleko.utils.is_method_GET():
        return flask.render_template('user/login.html',
                                     next=flask.request.args.get('next'))
    if pleko.utils.is_method_POST():
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

def do_login(username, password):
    """Set the session cookie if successful login.
    Raise ValueError if some problem.
    """
    user = get_user(username)
    if not werkzeug.security.check_password_hash(user['password'], password):
        raise ValueError
    if user['status'] != pleko.constants.ENABLED:
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
    if pleko.utils.is_method_GET():
        return flask.render_template('user/register.html')
    elif pleko.utils.is_method_POST():
        try:
            with UserContext() as ctx:
                ctx.set_username(flask.request.form.get('username'))
                ctx.set_email(flask.request.form.get('email'))
                ctx.set_role(pleko.constants.USER)
                ctx.set_password()
            user = ctx.user
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.register'))
        # Directly enabled; send code to the user.
        if user['status'] == pleko.constants.ENABLED:
            send_password_code(user, 'registration')
            flask.flash('User account created; check your email.')
        # Was set to 'pending'; send email to admins.
        else:
            message = flask_mail.Message(
                "{} user account pending".format(config['SITE_NAME']),
                recipients=db.get_admins_email())
            message.body = "To enable the user account, go to {}".format(
                pleko.utils.get_absolute_url('.account',
                                             values={'username': 
                                                     user['username']}))
            pleko.utils.mail.send(message)
            flask.flash('User account created; an email will be sent when'
                        ' it has been enabled by the admin.')
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/reset', methods=["GET", "POST"])
def reset():
    "Reset the password for a user account and send email."
    if pleko.utils.is_method_GET():
        return flask.render_template('user/reset.html')
    elif pleko.utils.is_method_POST():
        try:
            user = get_user(email=flask.request.form['email'])
            if user is None: raise KeyError
            if user['status'] != pleko.constants.ENABLED: raise KeyError
        except KeyError:
            pass
        else:
            with UserContext(user) as ctx:
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
        pleko.utils.get_absolute_url('.password', query=query))
    pleko.utils.mail.send(message)

@blueprint.route('/password', methods=["GET", "POST"])
def password():
    "Set the password for a user account, and login user."
    if pleko.utils.is_method_GET():
        return flask.render_template(
            'user/password.html',
            username=flask.request.args.get('username'),
            code=flask.request.args.get('code'))
    elif pleko.utils.is_method_POST():
        try:
            user = get_user(username=flask.request.form['username'])
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
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/account/<id:username>')
@login_required
def account(username):
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('index'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    enable_disable = is_admin_and_not_self(user)
    return flask.render_template('user/account.html',
                                 user=user,
                                 enable_disable=enable_disable)

@blueprint.route('/account/<id:username>/logs')
@login_required
def account_logs(username):
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('index'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    cursor = flask.g.db.cursor()
    sql = "SELECT prev, editor, remote_addr, user_agent, timestamp" \
          " FROM users_logs WHERE username=? ORDER BY timestamp DESC"
    cursor.execute(sql, (user['username'],))
    logs = [dict(prev=json.loads(row[0]),
                 editor=row[1],
                 remote_addr=row[2],
                 user_agent=row[3],
                 timestamp=row[4])
            for row in cursor]
    return flask.render_template('user/account_logs.html', user=user, logs=logs)

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
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('index'))
    if not is_admin_or_self(user):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    if pleko.utils.is_method_GET():
        return flask.render_template('user/edit.html',
                                     user=user,
                                     change_role=is_admin_and_not_self(user))
    elif pleko.utils.is_method_POST():
        with UserContext(user) as ctx:
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
@admin_required
def accounts():
    cursor = flask.g.db.cursor()
    sql = "SELECT username, email, password, apikey," \
          " role, status, profile, created, modified FROM users"
    cursor.execute(sql)
    users = [{'username': row[0],
              'email':    row[1],
              'password': row[2],
              'apikey':   row[3],
              'role':     row[4],
              'status':   row[5],
              'profile':  json.loads(row[6]),
              'created':  row[7],
              'modified': row[8]}
             for row in cursor]
    return flask.render_template('user/accounts.html', users=users)

@blueprint.route('/account/<id:username>/enable', methods=["POST"])
@login_required
@admin_required
def enable(username):
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('index'))
    with UserContext(user) as ctx:
        ctx.set_status(pleko.constants.ENABLED)
        ctx.set_password()
    send_password_code(user, 'enabled')
    return flask.redirect(flask.url_for('.account', username=username))

@blueprint.route('/account/<id:username>/disable', methods=["POST"])
@login_required
@admin_required
def disable(username):
    user = get_user(username=username)
    if user is None:
        flask.flash('no such user', 'error')
        return flask.redirect(flask.url_for('index'))
    with UserContext(user) as ctx:
        ctx.set_status(pleko.constants.DISABLED)
    return flask.redirect(flask.url_for('.account', username=username))


class UserContext:
    "Context for creating, modifying and saving a user account."

    def __init__(self, user=None):
        if user is None:
            if flask.current_app.config['USER_ENABLE_IMMEDIATELY']:
                status = pleko.constants.ENABLED
            else:
                status = pleko.constants.PENDING
            self.user = dict(status=status, 
                             created=pleko.utils.get_time())
            self.prev = dict()
        else:
            self.user = user
            self.prev = user.copy()
        self.db = pleko.utils.get_masterdb()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['username', 'email', 'role', 'status']:
            if not self.user.get(key):
                raise ValueError("invalid user: %s not set" % key)
        self.user['modified'] = pleko.utils.get_time()
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username=?",
                       (self.user['username'],))
        rows = list(cursor)
        with self.db:
            # Update user
            if rows[0][0]:
                sql = "UPDATE users SET email=?, password=?," \
                      " apikey=?, role=?, status=?, profile=?, modified=?" \
                      " WHERE username=?"
                self.db.execute(sql, (self.user['email'],
                                      self.user['password'],
                                      self.user.get('apikey'),
                                      self.user['role'],
                                      self.user['status'],
                                      json.dumps(self.user['profile'],
                                                 ensure_ascii=False),
                                      self.user['modified'],
                                      self.user['username']))
            # Add user
            else:
                sql = "INSERT INTO users" \
                      " (username, email, password, apikey, role," \
                      "  status, profile, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.db.execute(sql, (self.user['username'],
                                      self.user['email'],
                                      self.user['password'],
                                      self.user.get('apikey'),
                                      self.user['role'],
                                      self.user['status'],
                                      json.dumps(self.user.get('profile') or {},
                                                 ensure_ascii=False),
                                      self.user['created'], 
                                      self.user['modified']))
            # Add log entry
            try:
                del self.prev['modified']
            except KeyError:
                pass
            for key, value in self.user.items():
                try:
                    if value == self.prev[key]:
                        del self.prev[key]
                except KeyError:
                    pass
            try:
                password = self.prev['password']
            except KeyError:
                pass
            else:
                if not password.startswith('code:'):
                    self.prev['password'] = '***'
            sql = "INSERT INTO users_logs (username, prev, editor," \
                  " remote_addr, user_agent, timestamp)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
            try:
                editor = flask.g.user['username']
            except AttributeError:
                editor = None
            if flask.has_request_context():
                remote_addr = str(flask.request.remote_addr)
                user_agent = str(flask.request.user_agent)
            else:
                remote_addr = None
                user_agent = None
            self.db.execute(sql, (self.user['username'],
                                  json.dumps(self.prev, ensure_ascii=False),
                                  editor,
                                  remote_addr,
                                  user_agent,
                                  pleko.utils.get_time()))

    def set_username(self, username):
        if 'username' in self.user:
            raise ValueError('username cannot be changed')
        if not pleko.constants.IDENTIFIER_RX.match(username):
            raise ValueError('invalid username; must be an identifier')
        if get_user(username=username, db=self.db):
            raise ValueError('username already in use')
        self.user['username'] = username

    def set_email(self, email):
        if not pleko.constants.EMAIL_RX.match(email):
            raise ValueError('invalid email')
        if get_user(email=email, db=self.db):
            raise ValueError('email already in use')
        self.user['email'] = email
        if self.user.get('status') == pleko.constants.PENDING:
            for rx in flask.current_app.config['USER_ENABLE_EMAIL_WHITELIST']:
                if re.match(rx, email):
                    self.set_status(pleko.constants.ENABLED)
                    break

    def set_status(self, status):
        if status not in pleko.constants.USER_STATUSES:
            raise ValueError('invalid status')
        self.user['status'] = status

    def set_role(self, role):
        if role not in pleko.constants.USER_ROLES:
            raise ValueError('invalid role')
        self.user['role'] = role

    def set_password(self, password=None):
        "Set the password; a one-time code if no password provided."
        config = flask.current_app.config
        if password is None:
            self.user['password'] = "code:%s" % pleko.utils.get_iuid()
        else:
            if len(password) < config['MIN_PASSWORD_LENGTH']:
                raise ValueError('password too short')
            self.user['password'] = werkzeug.security.generate_password_hash(
                password, salt_length=config['SALT_LENGTH'])

    def set_apikey(self):
        "Set a new API key."
        self.user['apikey'] = pleko.utils.get_iuid()
