"Visualization API schema component."

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
