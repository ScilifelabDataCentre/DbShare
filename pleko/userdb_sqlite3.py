"Sqlite3 implementation of UserDb."

import json
import sqlite3

import flask

import pleko.constants
import pleko.utils
import pleko.userdb


class UserDb(pleko.userdb.BaseUserDb):
    "Sqlite3 implementation of user account database."

    def __init__(self, config):
        "Connect to the Sqlite3 database."
        self.config = config
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
                        " status TEXT NOT NULL,"
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
        "Return an iterator over all users; partial data."
        cursor = self.db.cursor()
        sql = "SELECT iuid, username, email, role, status FROM users"
        cursor.execute(sql)
        result = []
        for row in cursor:
            result.append({'iuid': row[0],
                           'username': row[1],
                           'email': row[2],
                           'role': row[3],
                           'status': row[4]})
        return iter(result)

    def __getitem__(self, identifier):
        """Get the user by identifier (username or email).
        Raise KeyError if no such user.
        """
        cursor = self.db.cursor()
        sql = "SELECT iuid, username, email, password, apikey, role, status," \
              " created, modified FROM users WHERE"
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
                        'role': row[5],
                        'status': row[6],
                        'created': row[7],
                        'modified': row[8]}
        raise KeyError('no such user')

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        sql = "SELECT email FROM users WHERE role=? AND status=?"
        cursor = self.db.cursor()
        cursor.execute(sql, (pleko.constants.ADMIN, pleko.constants.ENABLED))
        return [row[0] for row in cursor]

    def save(self, user):
        "Save the user data."
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username=?",
                       (user['username'],))
        rows = list(cursor)
        with self.db:
            if rows[0][0]:
                sql = "UPDATE users SET username=?, email=?, password=?," \
                      " apikey=?, role=?, status=?, created=?, modified=?" \
                      " WHERE iuid=?"
                self.db.execute(sql, (user['username'],
                                      user['email'],
                                      user['password'],
                                      user.get('apikey'),
                                      user['role'],
                                      user['status'],
                                      user['created'],
                                      user['modified'],
                                      user['iuid']))
            else:
                sql = "INSERT INTO users" \
                      " (iuid, username, email, password, apikey, role," \
                      " status, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                self.db.execute(sql, (user['iuid'],
                                      user['username'],
                                      user['email'],
                                      user['password'],
                                      user.get('apikey'),
                                      user['role'],
                                      user['status'],
                                      user['created'], 
                                      user['modified']))

    def log(self, user, prev, **kwargs):
        "Log the changes in user account from the previous values."
        sql = "INSERT INTO logs" \
              " (user, prev, editor, remote_addr, user_agent, timestamp)" \
              " VALUES (?, ?, ?, ?, ?, ?)"
        with self.db:
            self.db.execute(sql,
                            (user['username'],
                             json.dumps(prev),
                             kwargs.get('editor'),
                             kwargs.get('remote_addr'),
                             kwargs.get('user_agent'),
                             pleko.utils.get_time()))
