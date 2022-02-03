"Various utility functions and classes."

import csv
import datetime
import functools
import http.client
import io
import json
import os.path
import re
import sqlite3
import string
import threading
import time
import urllib.parse
import uuid

import flask
import flask_mail
import jinja2.utils
import jsonschema
import marko
import werkzeug.routing

import dbshare.lexer
from dbshare import constants


# Global instance of mail interface.
mail = flask_mail.Mail()

# Global instance of SQL lexer.
lexer = dbshare.lexer.Lexer(
    [
        {
            "type": "RESERVED",
            "regexp": r"(?i)SELECT|DISTINCT|ALL|FROM|AS|WHERE|ORDER|BY|AND|OR|NOT|"
            r"LIMIT|CREATE|VIEW",
            "convert": "upcase",
        },
        {"type": "INTEGER", "regexp": r"-?\d+", "convert": "integer"},
        {"type": "DELIMITER", "regexp": r"!=|>=|<=|[-+/*<>=\?\.,;\(\)]"},
        {"type": "WHITESPACE", "regexp": r"\s+", "skip": True},
        {"type": "IDENTIFIER", "regexp": r"(?i)[a-z]\w*"},
        {
            "type": "IDENTIFIER",
            "regexp": r"(?P<quotechar>[\'|\"])\S+(?P=quotechar)",
            "convert": "quotechar_strip",
        },
    ]
)


def login_required(f):
    "Decorator for checking if logged in. Redirect to login page if not."

    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.current_user:
            url = flask.url_for("user.login", next=flask.request.base_url)
            return flask.redirect(url)
        return f(*args, **kwargs)

    return wrap


def admin_required(f):
    """Decorator for checking if logged in and 'admin' role.
    Otherwise return status 401 Unauthorized.
    """

    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.is_admin:
            flask.abort(http.client.UNAUTHORIZED)
        return f(*args, **kwargs)

    return wrap


class NameConverter(werkzeug.routing.BaseConverter):
    "URL route converter for a name; simply check for valid identifier value."

    def to_python(self, value):
        if not constants.NAME_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value


class NameExt:
    "Helper class for NameExtConverter."

    def __init__(self, match):
        if not match:
            raise werkzeug.routing.ValidationError
        self.name = match.group(1)
        if match.group(2):
            self.ext = match.group(2).strip(".")
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
                return f"{value}.{value.ext}"
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


def get_cnx(dbname=None, write=False):
    """Return a new connection to the database by the given name.
    If 'dbname' is None, return a connection to the system database.
    If the database file does not exist, it will be created.
    The OS-level file permissions are set in DbSaver.
    """
    if dbname is None:
        dbname = constants.SYSTEM
    dbpath = get_dbpath(dbname)
    if write:
        cnx = sqlite3.connect(dbpath)
    else:
        path = f"file:{dbpath}?mode=ro"
        cnx = sqlite3.connect(dbpath, uri=True)
    cnx.row_factory = sqlite3.Row
    return cnx


def get_dbpath(dbname):
    "Return the full file path of the database given by name."
    return os.path.join(flask.current_app.config["DATABASES_DIR"], f"{dbname}.sqlite3")


def get_sorted_schema(db, entities="tables"):
    """Return a sorted list of the schema dictionaries for the tables or views
    using the 'name' element as sorting key."""
    return sorted(db[entities].values(), key=lambda d: d["name"])


def get_iuid():
    "Return a new IUID, which is a UUID4 pseudo-random string."
    return uuid.uuid4().hex


def to_bool(s):
    "Convert string value into boolean."
    if not s:
        return False
    return s.lower() in ("true", "t", "yes", "y")


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
        if chars[-1] in string.ascii_letters:
            chars.reverse()
            break
        chars.pop()
    else:
        raise ValueError("empty string")
    for pos, char in enumerate(chars):
        if char not in constants.NAME_CHARS:
            chars[pos] = "_"
    return "".join(chars)


def name_in_nocase(name, names):
    "Using a non-case sensitive comparison, is the 'name' among the 'names'?"
    return name.lower() in [n.lower() for n in names]


def chunks(l, n):
    "Return list l split into chunks of size n."
    for i in range(0, len(l), n):
        yield l[i : i + n]


def url_for(endpoint, **kwargs):
    """Same as 'flask.url_for', but with '_external' set to True.
    If a key argument '_query' is present, its dictionary value
    is URL encoded to query parameters appended to the URL.
    """
    query = kwargs.pop("_query", None)
    url = flask.url_for(endpoint, _external=True, **kwargs)
    if query:
        query = urllib.parse.urlencode(query)
        if "?" in query:
            url += "&" + query
        else:
            url += "?" + query
    return url


def url_for_rows(db, schema, external=False, csv=False):
    "Return the URL for the rows of the table or view."
    if schema["type"] == constants.TABLE:
        url = url_for("table.rows", dbname=db["name"], tablename=schema["name"])
    else:
        url = url_for("view.rows", dbname=db["name"], viewname=schema["name"])
    if csv:
        url += ".csv"
    return url


def url_for_unq(endpoint, **kwargs):
    """Same as 'flask.url_for', but with '_external' set to True,
    and %XX escapes replaced by their single-character equivalents.
    """
    return urllib.parse.unquote(url_for(endpoint, **kwargs))


def accept_json():
    "Return True if the header Accept contains the JSON content type."
    acc = flask.request.accept_mimetypes
    best = acc.best_match([constants.JSON_MIMETYPE, constants.HTML_MIMETYPE])
    return best == constants.JSON_MIMETYPE and acc[best] > acc[constants.HTML_MIMETYPE]


def get_json(**items):
    "Return the JSON structure adding standard entries."
    result = {"$id": flask.request.url, "timestamp": get_time()}
    result.update(items)
    return result


def jsonify(result, schema):
    """Return a Response object containing the JSON of 'result',
    adding a header Link to the schema given by its URL path.
    """
    response = flask.jsonify(result)
    link = f"<{flask.current_app.config['SCHEMA_BASE_URL']}{schema}>"
    response.headers.add("Link", link, rel="schema")
    return response


def http_GET():
    "Is the HTTP method GET?"
    return flask.request.method == "GET"


def http_POST(csrf=True):
    "Is the HTTP method POST? Check whether used for method tunneling."
    if flask.request.method != "POST":
        return False
    if flask.request.form.get("_http_method") in (None, "POST"):
        if csrf:
            check_csrf_token()
        return True
    else:
        return False


def http_PUT():
    "Is the HTTP method PUT? Is not tunneled."
    return flask.request.method == "PUT"


def http_DELETE(csrf=True):
    "Is the HTTP method DELETE? Check for method tunneling."
    if flask.request.method == "DELETE":
        return True
    if flask.request.method == "POST":
        if csrf:
            check_csrf_token()
        return flask.request.form.get("_http_method") == "DELETE"
    else:
        return False


def csrf_token():
    "Output HTML for cross-site request forgery (CSRF) protection."
    try:
        token = flask.session["_csrf_token"]
    except KeyError:
        # Generate a token to last the session's lifetime.
        token = flask.session["_csrf_token"] = get_iuid()
    html = f'<input type="hidden" name="_csrf_token" value="{token}">'
    return jinja2.utils.Markup(html)


def check_csrf_token():
    "Check the CSRF token for POST HTML."
    # Do not use up the token; keep it for the session's lifetime.
    token = flask.session.get("_csrf_token", None)
    if not token or token != flask.request.form.get("_csrf_token"):
        flask.abort(http.client.BAD_REQUEST)


def flash_error(msg):
    "Flash error message."
    flask.flash(str(msg), "error")


def flash_message(msg):
    "Flash information message."
    flask.flash(str(msg), "message")


def flash_message_limit(limit):
    "Flash message about limit on number of rows."
    flash_message(f"NOTE: The number of rows displayed is limited to {limit:,}.")


def informative(value):
    "Template filter: Informative representation of the value."
    if isinstance(value, bool):
        return repr(value)
    elif isinstance(value, int):
        return "{:,}".format(value)
    elif isinstance(value, float):
        return "{:3g}".format(value)
    elif isinstance(value, str):
        return repr(value)
    elif value is None:
        return "?"
    else:
        return value


def size_none(value):
    "Template filter: Size in bytes with thousands delimiters, or 'none'."
    if value is None:
        value = "<em>none</em>"
    else:
        value = '<span class="text-monospace">{:,}</span>'.format(value)
    return jinja2.utils.Markup(value)


def none_as_literal_null(value):
    "Template filter: Output None as HTML '<NULL>' in safe mode."
    if value is None:
        return jinja2.utils.Markup("<i>&lt;NULL&gt;</i>")
    else:
        return value


def none_as_empty_string(value):
    "Template filter: Output the value if not None, else an empty string."
    if value is None:
        return ""
    else:
        return value


class HtmlRenderer(marko.html_renderer.HTMLRenderer):
    """Extension of HTML renderer to allow setting <a> attribute '_target'
    to '_blank', when the title begins with an exclamation point '!'.
    """

    def render_link(self, element):
        if element.title and element.title.startswith("!"):
            template = '<a target="_blank" href="{}"{}>{}</a>'
            element.title = element.title[1:]
        else:
            template = '<a href="{}"{}>{}</a>'
        title = (
            ' title="{}"'.format(self.escape_html(element.title))
            if element.title
            else ""
        )
        url = self.escape_url(element.dest)
        body = self.render_children(element)
        return template.format(url, title, body)


def markdown2html(value):
    "Process the value from Markdown to HTML."
    return marko.Markdown(renderer=HtmlRenderer).convert(value or "")


def display_markdown(value):
    "Template filter: Use Markdown to process the value."
    return jinja2.utils.Markup(markdown2html(value))


def get_site_text(filename):
    """Get the Markdown-formatted text from a file in the site directory.
    Return None if no such file.
    """
    try:
        filepath = os.path.normpath(os.path.join(constants.ROOT, "../site", filename))
        with open(filepath) as infile:
            return infile.read()
    except (OSError, IOError):
        return None


def access(value):
    "Template filter: Output public or private according to the value."
    if value:
        return jinja2.utils.Markup('<span class="badge badge-info">public</span>')
    else:
        return jinja2.utils.Markup('<span class="badge badge-secondary">private</span>')


def mode(value):
    "Template filter: Output readonly or read-write according to the value."
    if value:
        return jinja2.utils.Markup('<span class="badge badge-success">read-only</span>')
    else:
        return jinja2.utils.Markup(
            '<span class="badge badge-warning">read/write</span>'
        )


def json_validate(instance, schema):
    "Validate the JSON instance versus the given JSON schema."
    jsonschema.validate(
        instance=instance,
        schema=schema,
        format_checker=jsonschema.draft7_format_checker,
    )


def abort_json(status_code, error):
    "Raise abort with given status code and error message."
    response = flask.Response(status=status_code)
    response.set_data(json.dumps({"message": str(error)}))
    flask.abort(response)


def _timeout_interrupt(cnx, event, timeout, increment, backoff):
    "Background thread to interrupt the Sqlite3 query when timeout."
    assert timeout > 0.0
    assert increment > 0.0
    assert backoff > 1.0
    event.wait()
    elapsed = 0.0
    while elapsed < timeout:
        if not event.is_set():
            return
        time.sleep(increment)
        elapsed += increment
        increment *= backoff
    cnx.interrupt()


def execute_timeout(cnx, command, **kwargs):
    """Perform Sqlite3 command to be interrupted if running too long.
    If the given command is a string, it is executed as SQL.
    If the command is a callable, call it with the cnx and any given
    keyword arguments.
    Raises SystemError if interrupted by timeout.
    """
    config = flask.current_app.config
    event = threading.Event()
    timeout = config["EXECUTE_TIMEOUT"]
    args = (
        cnx,
        event,
        timeout,
        config["EXECUTE_TIMEOUT_INCREMENT"],
        config["EXECUTE_TIMEOUT_BACKOFF"],
    )
    thread = threading.Thread(target=_timeout_interrupt, args=args)
    thread.start()
    event.set()
    try:
        if isinstance(command, str):  # SQL
            result = cnx.execute(command)
        elif callable(command):
            result = command(cnx, **kwargs)
    except sqlite3.ProgrammingError:
        raise
    except sqlite3.OperationalError as error:
        # This looks like a bug in the sqlite3 module:
        # SQL syntax error should raise sqlite3.ProgrammingError,
        # not sqlite3.OperationalError, which is what it does.
        # That's why the error message has to be checked.
        if str(error) == "interrupted":
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
            delimiter = ","
        self.outfile = io.StringIO()
        self.writer = csv.writer(self.outfile, delimiter=delimiter)
        if header:
            self.writer.writerow(header)

    def write_rows(self, rows):
        "Write the given rows."
        self.writer.writerows(rows)

    def getvalue(self):
        "Return the written data."
        return self.outfile.getvalue()
