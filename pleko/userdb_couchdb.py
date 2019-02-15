"CouchDB implementation of UserDb."

import couchdb2
import flask
import werkzeug.security

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
        }
    }
}


class UserDb(BaseUserDb):
    "CouchDB implementation of user account database."

    def __init__(self, config):
        "Connect to the CouchDB database server."
        if config.get('USERDB_SERVER') and config.get('USERDB_USERNAME'):
            server = couchdb2.Server(href=config['USERDB_SERVER'],
                                     username=config['USERDB_USERNAME'],
                                     password=config['USERDB_PASSWORD'])
        else:
            server = couchdb2.Server(href=config['USERDB_SERVER'])
        self.db = server[config['USERDB_DATABASE']]

    def initialize(self):
        """Initialize the database.
        Ensure up-to-date Mango-style indexes.
        """
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
                    flask.current_app.logger.debug("loading index %s %s",
                                                   ddocname,
                                                   indexname)
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

    def create(self, username, email, password, role):
        """Create a user account.
        Raise ValueError if any problem.
        """
        self.check_create(username, email, password, role)
        raise NotImplementedError
