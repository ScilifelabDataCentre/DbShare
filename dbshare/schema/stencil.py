"Stencil API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/stencil',
    '$schema': constants.SCHEMA_SCHEMA_URL,
    'title': 'Stencil API JSON schema.',
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
