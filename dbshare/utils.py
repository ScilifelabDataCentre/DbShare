"Various utility functions and classes."

import csv
import datetime
import http.client
import io
import json
import os.path
import re
import sqlite3
import threading
import time
import uuid

import flask
import flask_mail
import jinja2.utils
import werkzeug.routing

from dbshare.lexer import Lexer
from dbshare import constants


# Global instance of mail interface.
mail = flask_mail.Mail()

# Global instance of SQL lexer.
lexer = Lexer([
    {'type': 'RESERVED',
     'regexp': r"(?i)SELECT|DISTINCT|FROM|AS|ORDER|BY|AND|OR|NOT|LIMIT",
     'convert': 'upcase'},
    {'type': 'INTEGER', 'regexp': r"-?\d+", 'convert': 'integer'},
    {'type': 'DELIMITER', 'regexp': r"!=|>=|<=|[-+/*<>=\?\.,;\(\)]"},
    {'type': 'WHITESPACE', 'regexp': r"\s+", 'skip': True},
    {'type': 'IDENTIFIER', 'regexp': r"(?i)[a-z]\w*"},
    {'type': 'IDENTIFIER',
     'regexp': r"(?P<quotechar>[\'|\"])\S+(?P=quotechar)",
     'convert': 'quotechar_strip'}
])

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
            self.ext = match.group(2).strip('.').lower() # Case-insensitive
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

class Timer:
    "CPU timer."

    def __init__(self):
        self.start = time.process_time()

    def __call__(self):
        "Return CPU time (in seconds) since start of this timer."
        return time.process_time() - self.start

    @property
    def milliseconds(self):
        "Return CPU time (in milliseconds) since start of this timer."
        return round(1000 * self())


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

def url_for_rows(db, schema, external=False, csv=False):
    "Return the URL for the rows of the table or view."
    if schema['type'] == constants.TABLE:
        url = url_for('table.rows', dbname=db['name'], tablename=schema['name'])
    else:
        url = url_for('view.rows', dbname=db['name'], viewname=schema['name'])
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

def url_for(endpoint, **values):
    "Same as 'flask.url_for', but with '_external' set to True."
    return flask.url_for(endpoint, _external=True, **values)

def accept_json():
    "Return True if the header Accept contains the JSON content type."
    acc = flask.request.accept_mimetypes
    best = acc.best_match([constants.JSON_MIMETYPE, constants.HTML_MIMETYPE])
    return best == constants.JSON_MIMETYPE and \
        acc[best] > acc[constants.HTML_MIMETYPE]

def get_api(**items):
    "Return the JSON structure with standard additional items."
    result = {'$id': flask.request.url}
    result.update(items)
    result['timestamp'] = get_time()
    return result

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
    # Generate a token to last the session's lifetime.
    if '_csrf_token' not in flask.session:
        flask.session['_csrf_token'] = get_iuid()
    html = '<input type="hidden" name="_csrf_token" value="%s">' % \
           flask.session['_csrf_token']
    return jinja2.utils.Markup(html)

def check_csrf_token():
    "Check the CSRF token for POST HTML."
    # Do not use up the token; keep it for the session's lifetime.
    token = flask.session.get('_csrf_token', None)
    if not token or token != flask.request.form.get('_csrf_token'):
        flask.abort(http.client.BAD_REQUEST)

def flash_message_limit(limit):
    "Flash message about limit on number of rows."
    msg = f"NOTE: The number of rows displayed is limited to {limit:,}."
    flask.flash(msg, 'message')

def _timeout_interrupt(cnx, event, timeout, increment, backoff):
    "Background thread to interrupt the Sqlite3 query when timeout."
    assert timeout > 0.0
    assert increment > 0.0
    assert backoff > 1.0
    event.wait()
    elapsed = 0.0
    while elapsed < timeout:
        if not event.is_set(): return
        time.sleep(increment)
        elapsed += increment
        increment *= backoff
    cnx.interrupt()

def execute_timeout(cnx, command, **kwargs):
    """Perform Sqlite3 command(s) to be interrupted if running too long.
    If the given command is a string, it is executed as SQL and all rows
    produced by it are returned.
    If the command is a callable, call it with the cnx and any given
    keyword arguments.
    Raises SystemError if interrupted by timeout.
    """
    config = flask.current_app.config
    event = threading.Event()
    timeout = config['EXECUTE_TIMEOUT']
    args = (cnx, 
            event,
            timeout,
            config['EXECUTE_TIMEOUT_INCREMENT'],
            config['EXECUTE_TIMEOUT_BACKOFF'])
    thread = threading.Thread(target=_timeout_interrupt, args=args)
    thread.start()
    event.set()
    try:
        if isinstance(command, str): # SQL
            result = cnx.execute(command).fetchall()
        elif callable(command):
            result = command(cnx, **kwargs)
    except sqlite3.ProgrammingError:
        raise
    except sqlite3.OperationalError as error:
        # This looks like a bug in the sqlite3 module:
        # SQL syntax error should raise sqlite3.ProgrammingError,
        # not sqlite3.OperationalError, which is what it does.
        # That's why the error message has to be checked.
        if str(error) == 'interrupted':
            raise SystemError(f"execution exceeded {timeout} seconds; interrupted")
        else:
            raise
    event.clear()
    thread.join()
    return result


class CsvWriter:
    "Create CSV file content from rows of data."

    def __init__(self, header=None, delimiter=None):
        if delimiter is None:
            delimiter = ','
        self.outfile = io.StringIO()
        self.writer = csv.writer(self.outfile, delimiter=delimiter)
        if header:
            self.writer.writerow(header)

    def write_rows(self, rows, skip_first_column=False):
        "Write the given rows."
        if skip_first_column:
            for row in rows:
                self.writer.writerow(row[1:])
        else:
            self.writer.writerows(rows)

    def getvalue(self):
        "Return the written data."
        return self.outfile.getvalue()
