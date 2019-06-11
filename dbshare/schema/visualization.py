"JSON schema component for the visualization specification."

schema = {
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
