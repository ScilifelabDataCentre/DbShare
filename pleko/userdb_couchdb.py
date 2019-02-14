"CouchDB implementation of UserDb."

import json
import logging

import couchdb2

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
        }
    }
}


class UserDb:
    "User account database."

    def __init__(self, config):
        server = couchdb2.Server(href=config['USERDB_SERVER'],
                                 username=config['USERDB_USERNAME'],
                                 password=config['USERDB_PASSWORD'])
        self.db = server[config['USERDB_DATABASE']]

    def initialize(self):
        "Initialize the database; Mango-style indexes."
        current_indexes = self.db.get_indexes()['indexes']
        for ddocname, indexes in INDEXES.items():
            for indexname, indexdef in indexes.items():
                ok = False
                for current in current_indexes:
                    if current['ddoc'] == "_design/{}".format(ddocname) \
                       and current['name'] == indexname:
                        ok = current['def']['fields'] == indexdef['fields'] and \
                             current['def']['partial_filter_selector'] == indexdef['selector']
                if not ok:
                    logging.debug("loading index %s %s", ddocname, indexname)
                self.db.put_index(indexdef['fields'],
                                  ddoc=ddocname,
                                  name=indexname,
                                  selector=indexdef['selector'])

    def __getitem__(self, identifier):
        """Get the user by identifier (username or email).
        Raise KeyError if no such user.
        """
        result = db.db.find({'username': identifier},
                            use_index=[DDOCNAME, 'username'])
        if len(result['docs']) == 1:
            return result['docs'][0]
        result = db.db.find({'email': identifier},
                            use_index=[DDOCNAME, 'email'])
        if len(result['docs']) == 1:
            return result['docs'][0]
        raise KeyError

    def get(self, identifier, default=None):
        try:
            return self[identifier]
        except KeyError:
            return default

    def create(self, username, email, password, role):
        """Create a user account.
        Raise ValueError if any problem.
        """
        if not username:
            raise ValueError('no username provided')
        if self.get(username):
            raise ValueError('username already in use')
        if not email:
            raise ValueError('no email provided')
        if self.get(email):
            raise ValueError('email already in use')
        # XXX
