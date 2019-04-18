"Various utility functions and classes."

import csv
import datetime
import io
import json
import os.path
import sqlite3
import threading
import time
import urllib.parse
import uuid

import flask
import flask_mail
import jinja2.utils
import werkzeug.routing

from pleko import constants


mail = flask_mail.Mail()

class NameConverter(werkzeug.routing.BaseConverter):
    "URL route converter for a name."
    def to_python(self, value):
        if not constants.NAME_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value.lower()    # Case-insensitive

class NameExt:
    "Helper class for NameExtConverter."
    def __init__(self, match):
        if not match:
            raise werkzeug.routing.ValidationError
        self.name = match.group(1).lower() # Case-insensitive
        if match.group(2):
            self.ext = match.group(2).lstrip('.').lower() # Case-insensitive
        else:
            self.ext = None
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
    using the 'name' element as key."""
    return sorted(schemalist, key=lambda d: d['name'])

def dbpath(dbname, dirpath=None):
    "Return the file path for the given database name."
    if dirpath is None:
        dirpath = flask.current_app.config['DATABASES_DIRPATH']
    dirpath = os.path.expanduser(dirpath)
    dirpath = os.path.expandvars(dirpath)
    return os.path.join(dirpath, dbname) + '.sqlite3'

def get_url(endpoint, values={}, query={}):
    "Get the absolute URL for the endpoint, with optional query part."
    url = flask.url_for(endpoint, _external=True, **values)
    if query:
        url += '?' + urllib.parse.urlencode(query)
    return url

def url_for_rows(db, schema, external=False, csv=False):
    "Return the URL for the rows of the table or view."
    if schema['type'] == constants.TABLE:
        url = flask.url_for('table.rows',
                            dbname=db['name'],
                            tablename=schema['name'],
                            _external=external)
    else:
        url = flask.url_for('view.rows',
                            dbname=db['name'],
                            viewname=schema['name'],
                            _external=external)
    if csv:
        url += '.csv'
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

def name_cleaned(name):
    """Return a cleaned-up version of the name:
    1) Strip blanks at either ends.
    2) Remove first character(s) if offensive.
    3) Replace all other offensive characters with underscore.
    Raise ValueError if empty string.
    """
    chars = list(name.strip())
    chars.reverse()
    while chars:
        if chars[-1] in constants.string.ascii_letters:
            chars.reverse()
            break
        chars.pop()
    else:
        raise ValueError('empty string')
    for pos, char in enumerate(chars):
        if char not in constants.NAME_CHARS:
            chars[pos] = '_'
    return ''.join(chars)

def name_before_as(name):
    "Extract the part before 'AS', removing blanks and double-quotes."
    name = name.strip()
    try:
        pos = name.upper().index(' AS ')
        name = name[:pos]
    except ValueError:
        pass
    return name.strip().strip('"')

def name_after_as(name):
    "Extract the part after 'AS', removing blanks and double-quotes."
    name = name.strip()
    try:
        pos = name.upper().index(' AS ')
        name = name[pos+len(' AS '):]
    except ValueError:
        pass
    return name.strip().strip('"')

def http_GET():
    "Is the HTTP method GET?"
    return flask.request.method == 'GET'

def http_POST(csrf=True):
    "Is the HTTP method POST? Check whether used for method tunneling."
    if flask.request.method != 'POST': return False
    if flask.request.form.get('_http_method') in (None, 'POST'):
        if csrf: check_csrf_token()
        return True
    else:
        return False

def http_PUT():
    "Is the HTTP method PUT? Is not tunneled."
    return flask.request.method == 'PUT'

def http_DELETE(csrf=True):
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

def html_none(value):
    "Output the value if not None, else an empty string."
    if value is None:
        return ''
    else:
        return value

def _interrupt(cnx, event, timeout, increment):
    "Background thread to interrupt the Sqlite3 query, if timeout."
    assert timeout > 0.0
    assert increment > 0.0
    event.wait()
    elapsed = 0.0
    while elapsed < timeout:
        if not event.is_set(): return
        time.sleep(increment)
        elapsed += increment
    cnx.interrupt()

def execute_timeout(cnx, sql, *values):
    """Perform a query to be interrupted if it runs too long.
    Returns a cursor containing the results.
    Raises SystemError if interrupted by time-out.
    """
    timeout = flask.current_app.config['EXECUTE_TIMEOUT']
    increment = flask.current_app.config['EXECUTE_TIMEOUT_INCREMENT']
    event = threading.Event()
    thread = threading.Thread(target=_interrupt,
                              args=(cnx, event, timeout, increment))
    thread.start()
    event.set()
    cursor = cnx.cursor()
    try:
        cursor.execute(sql, values)
        result = cursor.fetchall()
    except sqlite3.OperationalError as error:
        raise SystemError(f"execution time exceeded {timeout} s; interrupted")
    event.clear()
    thread.join()
    return result

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

    def add_row(self, row):
        self.writer.writerow(row)

    def add_rows(self, rows, skip_rowid=False):
        if skip_rowid:
            for row in rows:
                self.writer.writerow(row[1:])
        else:
            self.writer.writerows(rows)

    def get(self):
        return self.outfile.getvalue()
