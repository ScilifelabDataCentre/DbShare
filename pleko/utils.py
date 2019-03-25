"Various utility functions and classes."

import datetime
import json
import os.path
import sqlite3
import urllib.parse
import uuid

import flask
import flask_mail
import jinja2.utils
import werkzeug.routing

from pleko import constants


mail = flask_mail.Mail()

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

def dbpath(dbid, dirpath=None):
    "Return the file path for the given database identifier."
    if dirpath is None:
        dirpath = flask.current_app.config['DATABASES_DIRPATH']
    dirpath = os.path.expanduser(dirpath)
    dirpath = os.path.expandvars(dirpath)
    return os.path.join(dirpath, dbid) + '.sqlite3'
    
def get_absolute_url(endpoint, values={}, query={}):
    "Get the absolute URL for the endpoint, with optional query part."
    url = flask.url_for(endpoint, _external=True, **values)
    if query:
        url += '?' + urllib.parse.urlencode(query)
    return url

def get_iuid():
    "Return a new IUID, which is a UUID4 pseudo-random string."
    return uuid.uuid4().hex

def to_bool(s):
    "Convert string value into boolean."
    if not s: return False
    s = s.lower()
    return s in ('true', 't', 'yes', 'y')

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
    "Output HTML for cross-site request forgery (CSRF) protection."
    if '_csrf_token' not in flask.session:
        flask.session['_csrf_token'] = get_iuid()
    html = '<input type="hidden" name="_csrf_token" value="%s">' % \
           flask.session['_csrf_token']
    return jinja2.utils.Markup(html)

def check_csrf_token():
    "Check the CSRF token for POST HTML."
    token = flask.session.pop('_csrf_token', None)
    if not token or token != flask.request.form.get('_csrf_token'):
        flask.abort(400)

def json_html(data):
    "Output data as JSON for HTML display."
    return jinja2.utils.Markup("<pre>%s</pre>" % json.dumps(data, indent=2))
