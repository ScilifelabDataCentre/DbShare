"Sqlite3 implementation of UserDb."

import sqlite3

import flask
import werkzeug.security

from pleko import constants
from pleko import utils
from pleko.userdb import BaseUserDb


class UserDb(BaseUserDb):
    "Sqlite3 implementation of user account database."

    def __init__(self, config):
        self.db = sqlite3.connect(config['USERDB_FILEPATH'])

    def initialize(self):
        """Initialize the database.
        Tables and indexes.
        """
        self.db.execute("CREATE TABLE IF NOT EXISTS users"
                        "(iuid TEXT PRIMARY KEY,"
                        " username TEXT NOT NULL UNIQUE,"
                        " email TEXT NOT NULL UNIQUE,"
                        " password TEXT,"
                        " role TEXT NOT NULL,"
                        " created TEXT NOT NULL,"
                        " modified TEXT NOT NULL)")

    def __getitem__(self, identifier):
        """Get the user by identifier (username or email).
        Raise KeyError if no such user.
        """
        cursor = self.db.cursor()
        sql = "SELECT iuid, username, email, password, role" \
              " FROM users WHERE"
        cursor.execute(sql + " username=?", (identifier,))
        rows = list(cursor)
        if len(rows) != 1:
            cursor.execute(sql + " email=?", (identifier,))
            rows = list(cursor)
            if len(rows) != 1:
                raise KeyError('no such user')
        row = rows[0]
        return {'iuid': row[0],
                'username': row[1],
                'email': row[2],
                'password': row[3],
                'role': row[4]}

    def create(self, username, email, password, role):
        """Create a user account.
        Raise ValueError if any problem.
        """
        self.check_create(username, email, password, role)
        iuid = utils.get_iuid()
        password = werkzeug.security.generate_password_hash(
            password, salt_length=self.config['SALT_LENGTH'])
        status = self.get_initial_status(email)
        with self.db:
            sql = "INSERT INTO users(iuid, username, email, password, role," \
                  "status, created, modified)"\
                  " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            now = utils.get_time()
            self.db.execute(sql, (iuid,
                                  username,
                                  email,
                                  password,
                                  role,
                                  status,
                                  now,
                                  now))
        return {'iuid': iuid,
                'username': username,
                'email': email,
                'role': role,
                'status': status,
                'created': now,
                'modified': now}
