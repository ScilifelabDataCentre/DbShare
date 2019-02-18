"Base abstract UserDb class; user account database."

import re

from pleko import constants


class BaseUserDb:
    "Base abstract UserDb class."

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

    def get(self, identifier, default=None):
        "Get the user by identifier (username of email); default if none."
        try:
            return self[identifier]
        except KeyError:
            return default

    def create(self, username, email, password,
               role=constants.USER, status=constants.DISABLED):
        """Create a user account and return the document.
        Raise ValueError if any problem.
        """
        raise NotImplementedError

    def check_create(self, username, email, password, role):
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
        if len(password) < self.config['MIN_PASSWORD_LENGTH']:
            raise ValueError('password is too short')
        if not role in constants.USER_ROLES:
            raise ValueError('invalid user role')

    def get_initial_status(self, email):
        "Get the initial status for the user given the email."
        if self.config['REGISTRATION_DIRECT']:
            return constants.ENABLED
        for pattern in self.config['REGISTRATION_WHITELIST']:
            if re.match(pattern, email):
                return constants.ENABLED
        return constants.DISABLED
