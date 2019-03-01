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
            "fields": [{"doc": "asc"}],
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
                self.db.put_index(indexdef['fields'],
                                  ddoc=ddocname,
                                  name=indexname,
                                  selector=indexdef['selector'])

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

    def __iter__(self):
        "Return an iterator over all users."
        result = self.db.find({'username': {'$gt': None}},
                              use_index=[DDOCNAME, 'username'])
        flask.current_app.logger.debug(result.get('warning'))
        return iter(result['docs'])

    def create(self, username, email, role):
        """Create a user account and return the document.
        Raise ValueError if any problem.
        """
        self.check_create(username, email, role)
        password = "code:{}".format(utils.get_iuid())
        status = self.get_initial_status(email)
        with UserSaver(self.db) as saver:
            saver['username'] = username
            saver['email'] = email
            saver['password'] = password
            saver['role'] = role
            saver['status'] = status
        return saver.doc

    def set_password(self, user, password):
        "Save the password, which is hashed within this method."
        password = self.hash_password(password)
        with UserSaver(self.db, doc=user) as saver:
            saver['password'] = password

    def set_status(self, user, status):
        "Set the status of the user account."
        with UserSaver(self.db, doc=user) as saver:
            saver['status'] = status

    def get_admins_email(self):
        "Get a list of email addresses to the admins."
        result = self.db.find({'role': constants.ADMIN},
                              use_index=[DDOCNAME, 'role'])
        return [user['email'] for user in result['docs']
                if user['status'] == constants.ENABLED]


class BaseSaver:
    "Context for creating or saving a document."

    TYPE = None

    def __init__(self, db, doc=None):
        self.db = db
        if doc is None:
            self.doc = {'type': self.TYPE,
                        'created': utils.get_time()}
        else:
            assert doc['type'] == self.TYPE
            self.doc = doc
        self.prev = {}

    def __getitem__(self, key):
        return self.doc[key]

    def __setitem__(self, key, value):
        try:
            prev = self[key]
            if prev == value: return
        except KeyError:
            pass
        else:
            self.prev[key] = prev
        self.doc[key] = value

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        self.doc['modified'] = utils.get_time()
        self.db.put(self.doc)
        self.write_log()

    def write_log(self):
        log = {'type': 'log',
               'doc': self.doc['_id'],
               'prev': self.prev,
               'timestamp': self.doc['modified']}
        try:
            log['username'] = flask.g.user['username']
        except AttributeError:
            pass
        try:
            log['remote_addr'] = str(flask.request.remote_addr)
            log['user_agent'] = str(flask.request.user_agent)
        except AttributeError:
            pass
        self.db.put(log)


class UserSaver(BaseSaver):
    TYPE = constants.USER
