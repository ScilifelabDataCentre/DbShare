"Visualization specification JSON schema component."

spec = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'title': {'type': ['string', 'null']},
        'specification': {'$ref': '#/definitions/link'},
    },
    'required': [
        'name',
        'title',
        'specification']
}
