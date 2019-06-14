"JSON schema definitions component."

schema = {
    'link': {
        'title': 'A link to an object.',
        'type': 'object',
        'properties': {
            'href': {'type': 'string', 'format': 'uri'},
            'content_type': {'type': 'string', 'default': 'application/json'},
            'format': {'type': 'string', 'default': 'json'}
        },
        'required': [
            'href'
        ]
    },
    'user': {
        'title': 'The owner of the current object.',
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'href': {'type': 'string', 'format': 'uri'}
        },
        'required': [
            'username',
            'href'
        ]
    }
}
