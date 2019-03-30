"Various utility functions and classes."

import csv
import datetime
import io
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

class NameConverter(werkzeug.routing.BaseConverter):
    "URL route converter for a name."
    def to_python(self, value):
        if not constants.NAME_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value

class NameExt:
    def __init__(self, match):
        if not match:
            raise werkzeug.routing.ValidationError
        self.name = match.group(1)
        if match.group(2):
            self.ext = match.group(2).lstrip('.')
        else:
            self.ext = None
        if self.ext not in constants.EXTS:
            raise werkzeug.routing.ValidationError
    def __str__(self):
        return self.name

class NameExtConverter(werkzeug.routing.BaseConverter):
    "URL route converter for a name with an optional extension."
    def to_python(self, value):
        return NameExt(constants.NAME_EXT_RX.match(value))
    def to_url(self, value):
        if isinstance(value, NameExt):
            if value.ext:
                return "%s.%s" % (value, value.ext)
        return str(value)

def get_cnx(path, write=False):
    "Return a new connection to the database at the given path."
    if write:
        cnx = sqlite3.connect(path)
        cnx.execute('PRAGMA foreign_keys=ON')
    else:
        path = "file:%s?mode=ro" % path
        cnx = sqlite3.connect(path, uri=True)
    return cnx

def sorted_schema(schemalist):
    """Return a sorted list of the list schema dictionaries
    according to the 'name' elements."""
    return sorted(schemalist, key=lambda d: d['name'])

def dbpath(dbname, dirpath=None):
    "Return the file path for the given database name."
    if dirpath is None:
        dirpath = flask.current_app.config['DATABASES_DIRPATH']
    dirpath = os.path.expanduser(dirpath)
    dirpath = os.path.expandvars(dirpath)
    return os.path.join(dirpath, dbname) + '.sqlite3'

def plotpath(dbname):
    "Return the file path for the plots of the given database."
    dirpath = flask.current_app.config['DATABASES_DIRPATH']
    dirpath = os.path.expanduser(dirpath)
    dirpath = os.path.expandvars(dirpath)
    return os.path.join(dirpath, '_plots_' + dbname) + '.json'

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


class CsvWriter:
    "Create CSV file content from rows of data."

    DELIMITERS = {',': ',',
                  '<tab>': '\t',
                  '\t': '\t',
                  '<space>': ' ',
                  ' ': ' ',
                  ':': ':',
                  ';': ';',
                  '|': '|'}

    def __init__(self, header=None, delimiter=None):
        if delimiter:
            try:
                delimiter = self.DELIMITERS[delimiter]
            except KeyError:
                raise ValueError('invalid CSV delimiter character')
        else:
            delimiter = ','
        self.outfile = io.StringIO()
        self.writer = csv.writer(self.outfile, delimiter=delimiter)
        if header:
            self.writer.writerow(header)

    def add_from_cursor(self, cursor):
        for row in cursor:
            self.writer.writerow(row)

    def add_row(self, row):
        self.writer.writerow(row)

    def get(self):
        return self.outfile.getvalue()
