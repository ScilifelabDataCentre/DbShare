"CouchDB implementation of ResourceDb."

import couchdb2

import flask

import pleko.constants
import pleko.resourcedb
import pleko.utils

DDOCNAME = 'mango'

INDEXES = {
    DDOCNAME: {
        "identifier": {
            "fields": [{"identifier": "asc"}],
            "selector": {"type": {"$eq": "resource"}}
        },
    }
}

class ResourceDb(pleko.resourcedb.BaseResourceDb):
    "CouchDB implementation of the resource database."

    def __init__(self, config):
        "Connect to the CouchDB database."
