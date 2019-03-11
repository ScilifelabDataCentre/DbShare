"Base abstract UserDb class; user account database."

import re

import flask
import werkzeug.security

import pleko.constants
import pleko.utils


class BaseUserDb:
    "Base abstract user database class."

    def __init__(self, config):
        "Connect to the database."
        raise NotImplementedError

    def initialize(self):
        "Initialize the database."
        pass

    def __iter__(self):
        "Return an iterator over all users."
        raise NotImplementedError

    def __getitem__(self, identifier):
        """Get the user by identifier (username, email or API key).
        Raise KeyError if no such user.
        """
        raise NotImplementedError

    def get(self, identifier, default=None):
        "Get the user by identifier (username of email); default if none."
        try:
            return self[identifier]
        except KeyError:
            return default

    def hash_password(self, password):
        "Return the hash of the password."
        return werkzeug.security.generate_password_hash(
            password, salt_length=self.config['SALT_LENGTH'])

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        raise NotImplementedError

    def save(self, user):
        "Save the user data."
        raise NotImplementedError

    def log(self, meta, user, prev):
        "Log the changes in user account from the previous values."
        raise NotImplementedError

    def get_logs(self, user):
        "Get the log entries for the user; sorted latest first."
        raise NotImplementedError

    def get_context(self, user=None):
        "Return a context for creating, modifying and save a user account."
        return UserContext(self, user=user)


class UserContext:
    "Context for creating, modifying and saving a user account."

    def __init__(self, userdb, user=None):
        self.userdb = userdb
        if user is None:
            if self.userdb.config['USER_ENABLE_IMMEDIATELY']:
                status = pleko.constants.ENABLED
            else:
                status = pleko.constants.PENDING
            self.user = dict(iuid=pleko.utils.get_iuid(),
                             status=status, 
                             created=pleko.utils.get_time())
            self.prev = dict()
        else:
            self.user = user
            self.prev = user.copy()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['username', 'email', 'role', 'status']:
            if not self.user.get(key):
                raise ValueError("invalid user: %s not set" % key)
        self.user['modified'] = pleko.utils.get_time()
        self.userdb.save(self.user)
        kwargs = dict()
        try:
            kwargs['editor'] = flask.g.user['username']
        except AttributeError:
            pass
        if flask.has_request_context():
            try:
                kwargs['remote_addr'] = str(flask.request.remote_addr)
                kwargs['user_agent'] = str(flask.request.user_agent)
            except AttributeError:
                pass
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
        self.userdb.log(self.user, self.prev, **kwargs)

    def set_username(self, username):
        if 'username' in self.user:
            raise ValueError('username cannot be changed')
        if not pleko.constants.IDENTIFIER_RX.match(username):
            raise ValueError('invalid username; must be an identifier')
        if self.userdb.get(username):
            raise ValueError('username already in use')
        self.user['username'] = username

    def set_email(self, email):
        if not pleko.constants.EMAIL_RX.match(email):
            raise ValueError('invalid email')
        if self.userdb.get(email):
            raise ValueError('email already in use')
        self.user['email'] = email
        if self.user.get('status') == pleko.constants.PENDING:
            for regexp in self.userdb.config['USER_ENABLE_EMAIL_WHITELIST']:
                if re.match(regexp, email):
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
        if password is None:
            self.user['password'] = "code:%s" % pleko.utils.get_iuid()
        else:
            if len(password) < self.userdb.config['MIN_PASSWORD_LENGTH']:
                raise ValueError('password too short')
            self.user['password'] = self.userdb.hash_password(password)

    def set_apikey(self):
        "Set a new API key."
        self.user['apikey'] = pleko.utils.get_iuid()
