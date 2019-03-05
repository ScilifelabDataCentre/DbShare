"CouchDB implementation of UserDb."

import couchdb2

import flask

from pleko import constants
from pleko import utils
from pleko.userdb import BaseUserDb

DDOCNAME = 'mango'

INDEXES = {
    DDOCNAME: {
        "username": {
            "fields": [{"username": "asc"}],
            "selector": {"type": {"$eq": "user"}}
        },
        "email": {
            "fields": [{"email": "asc"}],
            "selector": {"type": {"$eq": "user"}}
        },
        "role": {
            "fields": [{"role": "asc"}],
            "selector": {"type": {"$eq": "user"}}
        },
        "status": {
            "fields": [{"status": "asc"}],
            "selector": {"type": {"$eq": "user"}}
        },
        "log": {
            "fields": [{"user": "asc"}],
            "selector": {"type": {"$eq": "log"}}
        }
    }
}


class UserDb(BaseUserDb):
    "CouchDB implementation of user account database."

    def __init__(self, config):
        "Connect to the CouchDB database."
        if config.get('USERDB_SERVER') and config.get('USERDB_USERNAME'):
            server = couchdb2.Server(href=config['USERDB_SERVER'],
                                     username=config['USERDB_USERNAME'],
                                     password=config['USERDB_PASSWORD'])
        else:
            server = couchdb2.Server(href=config['USERDB_SERVER'])
        self.db = server[config['USERDB_DATABASE']]
        self.config = config

    def initialize(self):
        "Initialize the database. Mango-style indexes."
        current_indexes = self.db.get_indexes()['indexes']
        for ddocname, indexes in INDEXES.items():
            for indexname, indexdef in indexes.items():
                ok = False
                for current in current_indexes:
                    if current['ddoc'] == "_design/{}".format(ddocname) \
                       and current['name'] == indexname:
                        ok = current['def']['fields'] == indexdef['fields'] and \
                             current['def']['partial_filter_selector'] == indexdef['selector']
                self.db.put_index(indexdef['fields'],
                                  ddoc=ddocname,
                                  name=indexname,
                                  selector=indexdef['selector'])

    def __iter__(self):
        "Return an iterator over all users."
        result = self.db.find({'username': {'$gt': None}},
                              use_index=[DDOCNAME, 'username'])
        return iter(result['docs'])

    def __getitem__(self, identifier):
        """Get the user by identifier (username or email).
        Raise KeyError if no such user.
        """
        result = self.db.find({'username': identifier},
                              use_index=[DDOCNAME, 'username'])
        if len(result['docs']) == 1:
            return result['docs'][0]
        result = self.db.find({'email': identifier},
                              use_index=[DDOCNAME, 'email'])
        if len(result['docs']) == 1:
            return result['docs'][0]
        raise KeyError

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        result = self.db.find({'role': constants.ADMIN},
                              use_index=[DDOCNAME, 'role'])
        return [user['email'] for user in result['docs']
                if user['status'] == constants.ENABLED]

    def save(self, user):
        "Save the user data."
        if 'type' not in user:
            user['type'] = constants.USER
        if '_id' not in user:
            user['_id'] = user['iuid']
        self.db.put(user)

    def log(self, user, prev, **kwargs):
        "Log the changes in user account from the previous values."
        doc = dict(_id=utils.get_iuid(),
                   type='log',
                   user=user['username'],
                   prev=prev,
                   timestamp=utils.get_time())
        doc.update(kwargs)
        self.db.put(doc)
