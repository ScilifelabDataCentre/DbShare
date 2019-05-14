"DbShare API definitions part schema."

schema = {
    'link': {
        'type': 'object',
        'properties': {
            'href': {'type': 'string', 'format': 'uri'},
            'format': {'type': 'string', 'default': ' json'}
        },
        'required': ['href']
    },
    'user': {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'href': {'type': 'string', 'format': 'uri'}
        },
        'required': ['username', 'href']
    }
}
