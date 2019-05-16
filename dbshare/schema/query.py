"Query result API schema."

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'type': 'object',
    'properties': {
        'query': {
            'type': 'object',
            'properties': {
                'select': {'type': 'string'},
                'from': {'type': 'string'},
                'where': {'type': ['string', 'null']},
                'orderby': {'type': ['string', 'null']},
                'limit': {
                    'oneOf': [
                        {'type': 'null'},
                        {'type': 'integer', 'minimum': 1}
                    ]
                },
                'offset': {
                    'oneOf': [
                        {'type': 'null'},
                        {'type': 'integer', 'minimum': 1}
                    ]
                }
            },
            'required': [
                'select',
                'from'
            ]
        },
        'nrows': {'type': 'integer', 'mimimum': 0},
        'data': {
            'type': 'array',
            'items': {'type': 'object'}
        }
    }
}
