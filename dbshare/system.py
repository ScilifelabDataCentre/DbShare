"System database; metadata key/value, users, db list."

import datetime
import sqlite3

import flask

import dbshare
import dbshare.db

from . import constants
from . import utils


SYSTEM_TABLES = [
    dict(name='meta',
         columns=[dict(name='key', type=constants.TEXT, primarykey= True),
                  dict(name='value', type=constants.TEXT, notnull=True)
         ]
    ),
    dict(name='access_logs',
         columns=[dict(name='remote_addr', type=constants.TEXT),
                  dict(name='username', type=constants.TEXT),
                  dict(name='dbname', type=constants.TEXT),
                  dict(name='date', type=constants.TEXT),
                  dict(name='time', type=constants.TEXT),
                  dict(name='method', type=constants.TEXT),
                  dict(name='path', type=constants.TEXT),
                  dict(name='status_code', type=constants.INTEGER)
         ]
    ),
    dict(name='users',
         columns=[dict(name='username', type=constants.TEXT, primarykey= True),
                  dict(name='email', type=constants.TEXT, notnull=True),
                  dict(name='password', type=constants.TEXT),
                  dict(name='apikey', type=constants.TEXT),
                  dict(name='role', type=constants.TEXT, notnull=True),
                  dict(name='status', type=constants.TEXT, notnull=True),
                  dict(name='quota', type=constants.INTEGER),
                  dict(name='created', type=constants.TEXT, notnull=True),
                  dict(name='modified', type=constants.TEXT, notnull=True)
         ]
    ),
    dict(name='users_logs',
         columns=[dict(name='username', type=constants.TEXT, notnull=True),
                  dict(name='new', type=constants.TEXT, notnull=True),
                  dict(name='editor', type=constants.TEXT),
                  dict(name='remote_addr', type=constants.TEXT),
                  dict(name='user_agent', type=constants.TEXT),
                  dict(name='timestamp', type=constants.TEXT, notnull=True)
         ]
    ),
    dict(name='dbs',
         columns=[dict(name='name', type=constants.TEXT, primarykey=True),
                  dict(name='owner', type=constants.TEXT, notnull=True),
                  dict(name='title', type=constants.TEXT),
                  dict(name='description', type=constants.TEXT),
                  dict(name='public', type=constants.INTEGER, notnull=True),
                  dict(name='readonly', type=constants.INTEGER, notnull=True),
                  dict(name='created', type=constants.TEXT, notnull=True),
                  dict(name='modified', type=constants.TEXT, notnull=True)
         ]
    ),
    dict(name='dbs_hashes',
         columns=[dict(name='name', type=constants.TEXT, notnull=True),
                  dict(name='hashname', type=constants.TEXT, notnull=True),
                  dict(name='hashvalue', type=constants.TEXT, primarykey=True)
         ]
    ),
    dict(name='dbs_logs',
         columns=[dict(name='name', type=constants.TEXT, notnull=True),
                  dict(name='new', type=constants.TEXT, notnull=True),
                  dict(name='editor', type=constants.TEXT),
                  dict(name='remote_addr', type=constants.TEXT),
                  dict(name='user_agent', type=constants.TEXT),
                  dict(name='timestamp', type=constants.TEXT, notnull=True)
         ]
    ),
]

SYSTEM_INDEXES = [
    dict(name='users_email', table='users', columns=['email'], unique=True),
    dict(name='users_apikey', table='users', columns=['apikey']),
    dict(name='users_logs_username', table='users_logs', columns=['username']),
    dict(name='dbs_logs_id', table='dbs_logs', columns=['name']),
    dict(name='access_logs_remote_addr', table='access_logs', columns=['remote_addr']),
    dict(name='access_logs_username', table='access_logs', columns=['username']),
    dict(name='access_logs_dbname', table='access_logs', columns=['dbname']),
    dict(name='access_logs_date', table='access_logs', columns=['date']),
]

def log_access(response):
    "Add log entry for an access after response has been prepared."
    # Skip if access logging turned off.
    if not flask.current_app.config['LOG_ACCESS']:
        return response
    # Skip if access to '/static*'.
    if flask.request.path.startswith('/static'):
        return response
    with flask.g.syscnx:
        sql = "INSERT INTO access_logs (remote_addr, username," \
              " dbname, date, time, method, path, status_code)" \
              " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        if flask.g.current_user:
            username = flask.g.current_user['username']
        else:
            username = None
        dt = datetime.datetime.utcnow()
        values = [flask.request.remote_addr,
                  username,
                  getattr(flask.g, 'dbname', None),
                  dt.date().isoformat(),
                  dt.time().replace(microsecond=0).isoformat(),
                  flask.request.method,
                  flask.request.path,
                  response.status_code]
        flask.g.syscnx.execute(sql, values)
    return response

def init(app):
    "Initialize tables in the system database, if not done."
    path = utils.dbpath(constants.SYSTEM, 
                        dirpath=app.config['DATABASES_DIRPATH'])
    cnx = sqlite3.connect(path)
    for schema in SYSTEM_TABLES:
        sql = dbshare.db.get_sql_create_table(schema, if_not_exists=True)
        cnx.execute(sql)
    for schema in SYSTEM_INDEXES:
        sql = dbshare.db.get_sql_create_index(schema['table'], 
                                              schema, 
                                              if_not_exists=True)
        cnx.execute(sql)
    # Check or set major version number.
    major = dbshare.__version__.split('.')[0]
    cursor = cnx.cursor()
    sql = 'SELECT "value" FROM "meta" WHERE "key"=?'
    cursor.execute(sql, ('version',))
    rows = cursor.fetchall()
    if len(rows) == 1:
        if rows[0][0] != major:
            # Special case: upgrade from 1 to 2 can be done without changes.
            # This change entailed simply removing all charts-related stuff.
            if rows[0][0] == '1' and major == '2':
                with cnx:
                    sql = 'UPDATE "meta" SET value=? WHERE key=?'
                    cursor = cnx.execute(sql, (major, 'version'))
            else:
                raise ValueError('wrong major version of system database')
    else:
        with cnx:
            sql = 'INSERT INTO "meta" ("key", "value") VALUES (?, ?)'
            cnx.execute(sql, ('version', major))
    cnx.close()
    
