"CouchDB implementation of UserDb."

import json
import logging

import couchdb2

from pleko import settings

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

    def __init__(self):
        server = couchdb2.Server(href=settings.USER_DBI['SERVER'],
                                 username=settings.USER_DBI['USERNAME'],
                                 password=settings.USER_DBI['PASSWORD'])
        self.db = server[settings.USER_DBI['DATABASE']]

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


if __name__ == '__main__':
    settings.load()
    db = UserDb()
    db.initialize()
    result = db.db.find({'username': 'pekrau'},
                        use_index=[DDOCNAME, 'username'])
    print(json.dumps(result, indent=2))
