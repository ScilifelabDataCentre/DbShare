"DbShare API visualization part schema."

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
