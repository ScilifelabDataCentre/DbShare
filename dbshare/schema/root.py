"API root JSON schema."

from . import definitions
from .. import constants


input_output = {
    'type': 'object',
    'properties': {
        'content-type': {'type': 'string'},
        'schema': {
            'type': 'object',
            'properties': {
                'href': {'type': 'string',
                         'format': 'uri'}
            },
            'required': ['href']
        }
    },
    'required': ['content-type']
}

schema = {
    '$id': constants.SCHEMA_BASE_URL + '/root',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'timestamp': {'type': 'string', 'format': 'datetime'},
    'title': 'API root JSON schema.',
    'definitions': {
        'user': definitions.user_def,
        'link': definitions.link_def
    },
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'title': {'type': 'string'},
        'version': {'type': 'string',
                    'pattern': '^1\.[0-9]+\.[0-9]+$'},
        'databases': {
            'title': 'Links to collections of databases.',
            'type': 'object',
            'properties': {
                'all': {'title': 'Link to all databases.',
                        '$ref': '#/definitions/link'},
                'owner': {'title': 'Link to databases owned by the current user.',
                          '$ref': '#/definitions/link'},
                'public': {'title': 'Link to public databases.',
                           '$ref': '#/definitions/link'}},
            'required': ['public']
        },
        'templates': {
            'title': 'Links to collections of visualization templates.',
            'type': 'object',
            'properties': {
                'all': {'title': 'Link to all templates.',
                        '$ref': '#/definitions/link'},
                'owner': {'title': 'Link to templates owned by the current user.',
                          '$ref': '#/definitions/link'},
                'public': {'title': 'Link to public templates.',
                           '$ref': '#/definitions/link'}},
            'required': ['public']
        },
        'schema': {'title': 'Link to the schema documents.',
                   '$ref': '#/definitions/link'},
        'user': {'title': 'Link to the current user.',
                 '$ref': '#/definitions/user'},
        'operations': {
            'title': 'All URLs with non-GET methods specified by URI templates.',
            'type': 'object',
            'propertyNames': definitions.property_names,
            'properties': {
                'additionalProperties': {
                    'title': 'The property name is the type of entity the operation pertains to.',
                    'type': 'object',
                    'propertyNames': definitions.property_names,
                    'properties': {
                        'additionalProperties': {
                            'title': 'The property name is the operation.',
                            'type': 'object',
                            'properties': {
                                'title': {'type': 'string'},
                                'href': {'type': 'string', 'format': 'uri'},
                                'variables': {
                                    'type': 'object'
                                },
                                'method': {
                                    'type': 'string',
                                    'enum': ['POST', 'PUT', 'DELETE']
                                },
                                'input': input_output,
                                'output': input_output
                            },
                            'required': ['href', 'method']
                        }
                    }
                }
            }
        }
    },
    'required': [
        '$id',
        'timestamp',
        'title',
        'version',
        'databases',
        'templates',
        'schema'
    ]
}
