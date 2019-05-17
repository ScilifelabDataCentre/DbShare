"Definitions API schema component."

schema = {
    'link': {
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
