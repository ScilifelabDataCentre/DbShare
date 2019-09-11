"Chart API JSON schema."

from . import definitions
from .. import constants


schema = {
    '$id': constants.SCHEMA_BASE_URL + '/chart',
    '$schema': constants.SCHEMA_SCHEMA_URL,
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
