"Chart API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': '/chart',
    '$schema': constants.JSON_SCHEMA_URL,
    'title': 'Chart API JSON schema.',
    'definitions': {'link': definitions.link},
    'type': 'object',
    'properties': {
        '$id': {'type': 'string', 'format': 'uri'},
        'timestamp': {'type': 'string', 'format': 'date-time'},
        'name': {'type': 'string'},
        'source': {'type': 'string'},
        'spec': {'type': 'object'}
    },
    'required': [
        '$id',
        'timestamp',
        'name',
        'source',
        'spec'
    ],
    'additionalProperties': False
}

template_schema = {
    '$id': '/chart/template',
    '$schema': constants.JSON_SCHEMA_URL,
    'title': 'Chart template API JSON schema.',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': 'string'},
        'variables': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'title': {'type': ['string', 'null']},
                    'type': {
                        'oneOf': [
                            {'type': 'array',
                             'items': {'type': 'string'}},
                            {'type': 'string'}
                        ]
                    }
                },
                'required': [
                    'name',
                    'title',
                    'type'
                ],
                'additionalProperties': False
            }
        },
        'template': {'type': 'string'}
    },
    'required': [
        'name',
        'title',
        'variables',
        'template'
    ],
    'additionalProperties': False
}
