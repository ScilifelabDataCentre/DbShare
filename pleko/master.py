"Pleko master database."

import sqlite3

import flask

from pleko import constants
from pleko import utils
import pleko.db

MASTER_DBID = '_master'

MASTER_TABLES = [
    dict(id='users',
         columns=[dict(id='username', type=constants.TEXT, primarykey= True),
                  dict(id='email', type=constants.TEXT, notnull=True),
                  dict(id='password', type=constants.TEXT),
                  dict(id='apikey', type=constants.TEXT),
                  dict(id='role', type=constants.TEXT, notnull=True),
                  dict(id='status', type=constants.TEXT, notnull=True),
                  dict(id='created', type=constants.TEXT, notnull=True),
                  dict(id='modified', type=constants.TEXT, notnull=True)
         ]
    ),
    dict(id='users_logs',
         columns=[dict(id='username', type=constants.TEXT, notnull=True),
                  dict(id='new', type=constants.TEXT, notnull=True),
                  dict(id='editor', type=constants.TEXT),
                  dict(id='remote_addr', type=constants.TEXT),
                  dict(id='user_agent', type=constants.TEXT),
                  dict(id='timestamp', type=constants.TEXT, notnull=True)
         ],
         foreignkeys=[dict(id='users_fk',
                           columns=['username'],
                           ref='users',
                           refcolumns=['username'])]
    ),
    dict(id='dbs',
         columns=[dict(id='id', type=constants.TEXT, primarykey=True),
                  dict(id='owner', type=constants.TEXT, notnull=True),
                  dict(id='description', type=constants.TEXT),
                  dict(id='public', type=constants.INTEGER, notnull=True),
                  dict(id='tables', type=constants.TEXT, notnull=True),
                  dict(id='indexes', type=constants.TEXT, notnull=True),
                  dict(id='views', type=constants.TEXT, notnull=True),
                  dict(id='access', type=constants.TEXT, notnull=True),
                  dict(id='created', type=constants.TEXT, notnull=True),
                  dict(id='modified', type=constants.TEXT, notnull=True)
         ]),
    dict(id='dbs_logs',
         columns=[dict(id='id', type=constants.TEXT, notnull=True),
                  dict(id='new', type=constants.TEXT, notnull=True),
                  dict(id='editor', type=constants.TEXT),
                  dict(id='remote_addr', type=constants.TEXT),
                  dict(id='user_agent', type=constants.TEXT),
                  dict(id='timestamp', type=constants.TEXT, notnull=True)
         ],
         foreignkeys=[dict(id='dbs_fk',
                           columns=['id'],
                           ref='dbs',
                           refcolumns=['id'])]
    ),
]

MASTER_INDEXES = [
    dict(id='users_email', table='users', columns=['email'], unique=True),
    dict(id='users_apikey', table='users', columns=['apikey']),
    dict(id='users_logs_username', table='users_logs', columns=['username']),
    dict(id='dbs_logs_id', table='dbs_logs', columns=['id'])
]

def get_cnx(app=None):
    "Return the existing connection to the master database, else a new one."
    try:
        return flask.g.cnx
    except AttributeError:
        if app is None:
            app = flask.current_app
        cnx = sqlite3.connect(utils.dbpath(MASTER_DBID))
        cnx.execute('PRAGMA foreign_keys=ON')
        return cnx

def get_cursor(app=None):
    "Return a cursor for the master database."
    return get_cnx(app=app).cursor()

def init(app):
    "Initialize tables in the master database, if not done."
    cnx = sqlite3.connect(utils.dbpath(MASTER_DBID,
                                       dirpath=app.config['DATABASES_DIRPATH']))
    for schema in MASTER_TABLES:
        pleko.db.create_table(cnx, schema, if_not_exists=True)
    for schema in MASTER_INDEXES:
        pleko.db.create_index(cnx, schema, if_not_exists=True)
    cnx.close()
    
