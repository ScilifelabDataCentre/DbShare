"Sqlite3 implementation of UserDb."

import sqlite3

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

    def __iter__(self):
        "Return an iterator over all users."
        cursor = self.db.cursor()
        sql = "SELECT iuid, username, email, password, role"
        cursor.execute(sql)
        result = []
        for row in cursor:
            result.append({'iuid': row[0],
                           'username': row[1],
                           'email': row[2],
                           'password': row[3],
                           'role': row[4]})
        return iter(result)

    def create(self, username, email, role, status=None):
        """Create a user account.
        Raise ValueError if any problem.
        """
        self.check_create(username, email, role)
        iuid = utils.get_iuid()
        if status is None:
            status = self.get_initial_status(email)
        assert status in constants.USER_STATUSES
        with self.db:
            sql = "INSERT INTO users(iuid, username, email, password, role," \
                  "status, created, modified)" \
                  " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            now = utils.get_time()
            self.db.execute(sql, (iuid,
                                  username,
                                  email,
                                  self.get_password_code(),
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

    def set_password_code(self, user):
        "Set the password to a one-time code."
        with self.db:
            sql = "UPDATE users SET password=?, modified=? WHERE iuid=?"
            self.db.execute(sql, (self.get_password_code(),
                                  utils.get_time(),
                                  user['iuid']))

    def set_password(self, user, password):
        "Save the password, which is hashed within this method."
        password = self.hash_password(password)
        with self.db:
            sql = "UPDATE users SET password=?, modified=? WHERE iuid=?"
            self.db.execute(sql, (password, utils.get_time(), user['iuid']))

    def set_status(self, user, status):
        "Set the status of the user account."
        with self.db:
            sql = "UPDATE users SET status=?, modified=? WHERE iuid=?"
            self.db.execute(sql, (status, utils.get_time(), user['iuid']))

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        sql = "SELECT email FROM users WHERE role=? AND status=?"
        cursor = self.db.cursor()
        cursor.execute(sql, (constants.ADMIN, constants.ENABLED))
        return [row[0] for row in cursor]
