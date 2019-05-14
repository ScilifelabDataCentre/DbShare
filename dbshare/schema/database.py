"DbShare API databases part schema."

schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'owner': {'$ref': '#/definitions/user'},
        'public': {'type': 'boolean'},
        'readonly': {'type': 'boolean'},
        'size': {'type': 'integer'},
        'modified': {'type': 'string', 'format': 'timestamp'},
        'created': {'type': 'string', 'format': 'timestamp'},
        'href': {'type': 'string', 'format': 'uri'}
    },
    'required': ['name',
                 'title',
                 'owner',
                 'public',
                 'readonly',
                 'size',
                 'modified',
                 'created',
                 'href']
}
