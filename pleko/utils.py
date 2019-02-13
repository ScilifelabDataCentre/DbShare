"Various utility functions and classes."

import collections
import datetime
import functools
import json
import os
import urllib
import uuid

import flask
# import jsonschema
# from jsonschema import Draft4Validator as SchemaValidator
# import requests
import werkzeug.routing

import constants

def url(name, **kwargs):
    "Get the absolute URL for the named resource."
    return flask.url_for(name, _external=True, **kwargs)

def login_required(f):
    "Decorator for checking if logged in. Send to login page if not."
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.user:
            url = flask.url_for('login')
            query = urllib.parse.urlencode({'next': flask.request.base_url})
            url += '?' + query
            return flask.redirect(url)
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    """Decorator for checking if logged in and 'admin' role.
    Otherwise status 403 Forbidden.
    """
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.is_admin:
            flask.abort(403)
        return f(*args, **kwargs)
    return wrap

class IuidConverter(werkzeug.routing.BaseConverter):
    "URL route converter for an IUID."
    def to_python(self, value):
        if not constants.IUID_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value

class IdentifierConverter(werkzeug.routing.BaseConverter):
    "URL route converter for an identifier."
    def to_python(self, value):
        if not constants.IDENTIFIER_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value

def is_identifier(s):
    "Is the string value a valid identifier value?"
    return bool(constants.IDENTIFIER_RX.match(s))

def get_iuid():
    "Return a new IUID, which is a UUID4 pseudo-random string."
    return uuid.uuid4().hex

def get_time(offset=None):
    """Current date and time (UTC) in ISO format, with millisecond precision.
    Add the specified offset in seconds, if given.
    """
    instant = datetime.datetime.utcnow()
    if offset:
        instant += datetime.timedelta(seconds=offset)
    instant = instant.isoformat()
    return instant[:17] + "{:06.3f}".format(float(instant[17:])) + "Z"

def check(item, access_func=None, **kwargs):
    """Raise HTTP 404 if no item.
    Raise HTTP 403 if access_func evaluates to False.
    """
    if not item:
        flask.abort(404)
    if access_func and not access_func(item, **kwargs):
        flask.abort(403)

def is_method_GET():
    "Is the HTTP method GET?"
    return flask.request.method == 'GET'

def is_method_POST(csrf=True):
    "Is the HTTP method POST? Check whether used for method tunneling."
    if flask.request.method != 'POST': return False
    if flask.request.form.get('_http_method') in (None, 'POST'):
        if csrf: check_csrf_token()
        return True
    else:
        return False

def is_method_PUT():
    "Is the HTTP method PUT? Is not tunneled."
    return flask.request.method == 'PUT'

def is_method_DELETE(csrf=True):
    "Is the HTTP method DELETE? Check for method tunneling."
    if flask.request.method == 'DELETE': return True
    if flask.request.method == 'POST':
        if csrf: check_csrf_token()
        return flask.request.form.get('_http_method') == 'DELETE'
    else:
        return False

def csrf_token():
    """Output HTML for cross-site request forgery (CSRF) protection.
    Must be used with filter 'safe'."""
    if '_csrf_token' not in flask.session:
        flask.session['_csrf_token'] = get_iuid()
    return '<input type="hidden" name="_csrf_token">{}</input>'.format(
        flask.session['_csrf_token'])

def check_csrf_token():
    "Check the CSRF token for POST HTML."
    token = flask.session.pop('_csrf_token', None)
    if not token or token != flask.request.form.get('_csrf_token'):
        flask.abort(400)

def json_accepted():
    "Check the Accept header of the request if JSON is requested."
    accept_mimetypes = flask.request.accept_mimetypes
    best = accept_mimetypes.best_match([constants.JSON_MIMETYPE,
                                        constants.HTML_MIMETYPE])
    return (best == constants.JSON_MIMETYPE and
            accept_mimetypes[best] > accept_mimetypes[constants.HTML_MIMETYPE])

def render_json(data, status=200):
    "Return a JSON-encoded response."
    if data:
        result = collections.OrderedDict()
        result['@context'] = 'http://pleko.org/api/v1/context'
        result['@id'] = flask.request.url
        for key in data:
            result[key] = data[key]
        result.setdefault('links', {})['home'] = {'rel': 'home',
                                                  'href': url('apiv1.home')}
        response = flask.json.jsonify(result)
        response.status_code = status
        return response
    else:
        data = ''
    return (data, status, {'Content-Type': constants.JSON_MIMETYPE})

def display_value(value, input=False):
    "Format value for HTML display."
    if value is None:
        if input:
            return ''
        else:
            return '<i>null</i>'
    elif value == '':
        if input:
            return ''
        else:
            return "''"
    elif isinstance(value, dict):
        if input:
            return json.dumps(value, indent=2)
        else:
            return "<pre>{}</pre>".format(json.dumps(value, indent=2))
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)

def dictdiff(old, new):
    """Return a representation of differences between the two dictionaries.
    Recursively analyses values that are dictionaries,
    but not dictionaries that are part of list of tuple values.
    """
    old_keys = set(old)
    new_keys = set(new)
    result = {}
    added = dict([(k, new[k]) for k in new_keys.difference(old_keys)])
    if added:
        result['added'] = added
    removed = dict([(k, old[k]) for k in old_keys.difference(new_keys)])
    if removed:
        result['removed'] = removed
    changed = {}
    for key in new_keys.intersection(old_keys):
        old_value = old[key]
        new_value = new[key]
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            down = dictdiff(old_value, new_value)
            if down:
                changed[key] = down
        elif old_value != new_value:
            changed[key] = old_value
    if changed:
        result['changed'] = changed
    return result
