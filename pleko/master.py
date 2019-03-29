"Pleko master database."

import sqlite3

import flask

from pleko import constants
from pleko import utils
import pleko.db

MASTER_DBNAME = '_master'

MASTER_TABLES = [
    dict(name='users',
         columns=[dict(name='username', type=constants.TEXT, primarykey= True),
                  dict(name='email', type=constants.TEXT, notnull=True),
                  dict(name='password', type=constants.TEXT),
                  dict(name='apikey', type=constants.TEXT),
                  dict(name='role', type=constants.TEXT, notnull=True),
                  dict(name='status', type=constants.TEXT, notnull=True),
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
         ],
         foreignkeys=[dict(name='users_fk',
                           columns=['username'],
                           ref='users',
                           refcolumns=['username'])]
    ),
    dict(name='dbs',
         columns=[dict(name='name', type=constants.TEXT, primarykey=True),
                  dict(name='owner', type=constants.TEXT, notnull=True),
                  dict(name='description', type=constants.TEXT),
                  dict(name='tables', type=constants.TEXT, notnull=True),
                  dict(name='indexes', type=constants.TEXT, notnull=True),
                  dict(name='views', type=constants.TEXT, notnull=True),
                  dict(name='public', type=constants.INTEGER, notnull=True),
                  dict(name='access', type=constants.TEXT, notnull=True),
                  dict(name='readonly', type=constants.INTEGER, notnull=True),
                  dict(name='created', type=constants.TEXT, notnull=True),
                  dict(name='modified', type=constants.TEXT, notnull=True)
         ]),
    dict(name='dbs_logs',
         columns=[dict(name='name', type=constants.TEXT, notnull=True),
                  dict(name='new', type=constants.TEXT, notnull=True),
                  dict(name='editor', type=constants.TEXT),
                  dict(name='remote_addr', type=constants.TEXT),
                  dict(name='user_agent', type=constants.TEXT),
                  dict(name='timestamp', type=constants.TEXT, notnull=True)
         ],
         foreignkeys=[dict(name='dbs_fk',
                           columns=['name'],
                           ref='dbs',
                           refcolumns=['name'])]
    ),
]

MASTER_INDEXES = [
    dict(name='users_email', table='users', columns=['email'], unique=True),
    dict(name='users_apikey', table='users', columns=['apikey']),
    dict(name='users_logs_username', table='users_logs', columns=['username']),
    dict(name='dbs_logs_id', table='dbs_logs', columns=['name'])
]

def get_cnx(write=False):
    """Return the existing connection to the master database, else a new one.
    If write is true, then assume the old connection is read-only,
    so close it and open a new one.
    """
    if write:
        try:
            flask.g.cnx.close()
        except AttributeError:
            pass
        flask.g.cnx = utils.get_cnx(utils.dbpath(MASTER_DBNAME), write=True)
    try:
        return flask.g.cnx
    except AttributeError:
        flask.g.cnx = utils.get_cnx(utils.dbpath(MASTER_DBNAME))
        return flask.g.cnx

def get_cursor(write=False):
    "Return a cursor for the master database."
    return get_cnx(write=write).cursor()

def init(app):
    "Initialize tables in the master database, if not done."
    path = utils.dbpath(MASTER_DBNAME, dirpath=app.config['DATABASES_DIRPATH'])
    cnx = sqlite3.connect(path)
    for schema in MASTER_TABLES:
        pleko.db.create_table(cnx, schema, if_not_exists=True)
    for schema in MASTER_INDEXES:
        pleko.db.create_index(cnx, schema, if_not_exists=True)
    cnx.close()
    
