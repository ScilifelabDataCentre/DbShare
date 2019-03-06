"Sqlite3 implementation of UserDb."

import sqlite3

from pleko import constants
from pleko import utils
from pleko.userdb import BaseUserDb


class UserDb(BaseUserDb):
    "Sqlite3 implementation of user account database."

    def __init__(self, config):
        "Connect to the Sqlite3 database."
        self.db = sqlite3.connect(config['USERDB_FILEPATH'])

    def initialize(self):
        "Initialize the database. Tables and indexes."
        self.db.execute("CREATE TABLE IF NOT EXISTS users"
                        "(iuid TEXT PRIMARY KEY,"
                        " username TEXT NOT NULL UNIQUE,"
                        " email TEXT NOT NULL UNIQUE,"
                        " password TEXT,"
                        " apikey TEXT,"
                        " role TEXT NOT NULL,"
                        " created TEXT NOT NULL,"
                        " modified TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS logs"
                        "(user TEXT NOT NULL,"
                        " prev TEXT NOT NULL,"
                        " editor TEXT,"
                        " remote_addr TEXT,"
                        " user_agent TEXT,"
                        " timestamp TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS logs_user_ix"
                        " ON logs (user)")

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

    def __getitem__(self, identifier):
        """Get the user by identifier (username or email).
        Raise KeyError if no such user.
        """
        cursor = self.db.cursor()
        sql = "SELECT iuid, username, email, password, apikey, role," \
              " FROM users WHERE"
        for key in ['username', 'email', 'apikey']:
            cursor.execute(sql + " %s=?" % key, (identifier,))
            rows = list(cursor)
            if len(rows) == 1:
                row = rows[0]
                return {'iuid': row[0],
                        'username': row[1],
                        'email': row[2],
                        'password': row[3],
                        'apikey': row[4],
                        'role': row[5]}
        raise KeyError('no such user')

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        sql = "SELECT email FROM users WHERE role=? AND status=?"
        cursor = self.db.cursor()
        cursor.execute(sql, (constants.ADMIN, constants.ENABLED))
        return [row[0] for row in cursor]

    def save(self, user):
        "Save the user data."
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username=?",
                       (user['username']))
        rows = list(cursor)
        if rows[0][0]:
            sql = "INSERT INTO users" \
                  " (iuid, username, email, password, apikey, role," \
                  " status, created, modified)" \
                  " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(sql, (user['iuid'],
                                 user['username'],
                                 user['email'],
                                 user['password'],
                                 user.get('apikey'),
                                 user['role'],
                                 user['status'],
                                 user['created'], 
                                 user['modified']))
        else:
            sql = "UPDATE users SET username=?, email=?, password=?, apikey=?,"\
                  " role=?, status=?, created=?, modified=? WHERE iuid=?"
            cursor.execute(sql, (user['username'],
                                 user['email'],
                                 user['password'],
                                 user.get('apikey'),
                                 user['role'],
                                 user['status'],
                                 user['created'],
                                 user['modified'],
                                 user['iuid']))

    def log(self, user, prev, **kwargs):
        "Log the changes in user account from the previous values."
        sql = "INSERT INTO logs" \
              " (user, prev, editor, remote_addr, user_agent, timestamp)" \
              " VALUES (?, ?, ?, ?, ?, ?)"
        self.db.execute(sql,
                        (user['username'],
                         flask.jsonify(prev),
                         kwargs.get('editor'),
                         kwargs.get('remote_addr'),
                         kwargs.get('user_agent'),
                         utils.get_time()))
