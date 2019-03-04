"Base abstract UserDb class; user account database."

import re

import flask
import werkzeug.security

from pleko import constants
from pleko import utils


class BaseUserDb:
    "Base abstract user database class."

    def __init__(self, config):
        "Connect to the database."
        raise NotImplementedError

    def initialize(self):
        "Initialize the database."
        pass

    def __getitem__(self, identifier):
        """Get the user by identifier (username or email).
        Raise KeyError if no such user.
        """
        raise NotImplementedError

    def __iter__(self):
        "Return an iterator over all users."
        raise NotImplementedError

    def get(self, identifier, default=None):
        "Get the user by identifier (username of email); default if none."
        try:
            return self[identifier]
        except KeyError:
            return default

    def create(self, username, email, role, status=None):
        """Create a user account and return the document.
        Raise ValueError if any problem.
        """
        raise NotImplementedError

    def check_create(self, username, email, role):
        """Check the values given for creating a user account.
        Raise ValueError if any problem.
        """
        if not username:
            raise ValueError('no username provided')
        if not constants.IDENTIFIER_RX.match(username):
            raise ValueError('invalid username; must be an identifier')
        if self.get(username):
            raise ValueError('username already in use')
        if not email:
            raise ValueError('no email provided')
        if not constants.EMAIL_RX.match(email):
            raise ValueError('invalid email')
        if self.get(email):
            raise ValueError('email already in use')
        if not role in constants.USER_ROLES:
            raise ValueError('invalid user role')

    def set_password_code(self, user):
        "Set the password to a one-time code."
        raise NotImplementedError

    def get_password_code(self):
        "Get a one-time code for the password slot."
        return "code:{}".format(utils.get_iuid())

    def set_password(self, user, password):
        "Save the password, which is hashed within this method."
        raise NotImplementedError

    def hash_password(self, password):
        "Return the hash of the password."
        return werkzeug.security.generate_password_hash(
            password,
            salt_length=flask.current_app.config['SALT_LENGTH'])

    def set_status(self, user, status):
        "Set the status of the user account."
        raise NotImplementedError

    def get_initial_status(self, email):
        "Get the initial status for the user given the email."
        if self.config['REGISTRATION_DIRECT']:
            return constants.ENABLED
        for pattern in self.config['REGISTRATION_REGEXP_WHITELIST']:
            if re.match(pattern, email):
                return constants.ENABLED
        return constants.PENDING

    def save(self, user):
        "Save the user data."
        raise NotImplementedError

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        raise NotImplementedError
