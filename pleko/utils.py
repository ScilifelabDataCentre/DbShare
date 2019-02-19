"Various utility functions and classes."

import collections
import datetime
import functools
import json
import os
import urllib
import uuid

import flask
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
    return '<input type="hidden" name="_csrf_token" value="{}">'.format(
        flask.session['_csrf_token'])

def check_csrf_token():
    "Check the CSRF token for POST HTML."
    token = flask.session.pop('_csrf_token', None)
    if not token or token != flask.request.form.get('_csrf_token'):
        flask.abort(400)
