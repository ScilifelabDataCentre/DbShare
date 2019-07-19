"Configuration."

import os
import os.path
import sqlite3

import dbshare


ROOT_DIRPATH = os.path.dirname(os.path.abspath(__file__))

# Default configurable values; modified by reading JSON file in 'init'.
CONFIG = dict(
    VERSION = dbshare.__version__,
    SERVER_NAME = '127.0.0.1:5000',
    DATABASES_DIRPATH = 'data',
    SITE_NAME = 'DbShare',
    SITE_STATIC_DIRPATH = None,
    HOST_LOGO = None,           # Filename, must be in 'SITE_STATIC_DIRPATH'
    HOST_NAME = None,
    HOST_URL = None,
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    JSONIFY_AS_ASCII = False,
    JSON_SORT_KEYS = False,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # List of regexp's
    USER_DEFAULT_QUOTA = 2**22,       # 4 megabyte
    TABLE_INITIAL_COLUMNS = 8,
    MAX_NROWS_DISPLAY = 2000,
    CONTENT_HASHES = ['md5', 'sha1'],
    QUERY_DEFAULT_LIMIT = 200,
    # Suggested values for timeout, increment and backoff.
    # t=2.0, i=0.010, b=1.75
    #        i=0.014, b=1.55
    #        i=0.022, b=1.55
    # t=3.0, i=0.012, b=1.50
    #        i=0.014, b=1.95
    #        i=0.022, b=1.80
    # t=4.0, i=0.010, b=1.45
    #        i=0.014, b=1.70
    #        i=0.020, b=1.75
    EXECUTE_TIMEOUT           = 2.0,
    EXECUTE_TIMEOUT_INCREMENT = 0.010,
    EXECUTE_TIMEOUT_BACKOFF   = 1.75,
    CHART_DEFAULT_WIDTH = 400,
    CHART_DEFAULT_HEIGHT = 400,
    COLUMN_ANNOTATIONS = ['quantitative', 'temporal', 
                          'ordinal', 'nominal', 'ignore'],
    CSV_FILE_DELIMITERS = {'comma': {'label': "comma ','", 'char': ','},
                           'tab': {'label': "tab '\\t'", 'char': '\t'},
                           'semicolon': {'label': "semicolon ';'", 'char': ';'},
                           'vertical-bar': {'label': "vertical-bar '|'", 
                                            'char': '|'},
                           'colon': {'label': "colon ':'", 'char': ':'}},
    SQLITE_VERSION = sqlite3.sqlite_version,
    JSONSCHEMA_URL = 'http://json-schema.org/draft-07/schema#',
    MARKDOWN_SYNTAX_URL = 'https://daringfireball.net/projects/markdown/syntax',
    # Bootstrap
    BOOTSTRAP_VERSION = '4.3.1',
    BOOTSTRAP_CSS_ATTRS = 'href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous"',
    POPPER_JS_ATTRS = 'src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"',
    BOOTSTRAP_JS_ATTRS = 'src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"',
    # jQuery
    JQUERY_VERSION = '3.3.1',
    JQUERY_JS_ATTRS = 'src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"',
    # DataTables
    DATATABLES_CSS_URL = 'https://cdn.datatables.net/1.10.18/css/dataTables.bootstrap4.min.css',
    DATATABLES_JS_URL = 'https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js',
    DATATABLES_BOOTSTRAP_JS_URL = 'https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js',
    DATATABLES_VERSION = '1.10.18',
    # Vega and Vega-Lite
    VEGA_JS_URL = 'https://cdn.jsdelivr.net/npm/vega@5',
    VEGA_SCHEMA_URL = 'https://vega.github.io/schema/vega/v5.json',
    VEGA_SCHEMA = os.path.join(ROOT_DIRPATH, 'schema/vega-v5.json'),
    VEGA_VERSION = '5',
    VEGA_DEFAULT_WIDTH = 400,
    VEGA_DEFAULT_HEIGHT = 400,
    VEGA_EMBED_JS_URL = 'https://cdn.jsdelivr.net/npm/vega-embed@4',
    VEGA_LITE_JS_URL = 'https://cdn.jsdelivr.net/npm/vega-lite@3',
    VEGA_LITE_SCHEMA_URL = 'https://vega.github.io/schema/vega-lite/v3.json',
    VEGA_LITE_SCHEMA = os.path.join(ROOT_DIRPATH, 'schema/vega-lite-v3.json'),
    VEGA_LITE_VERSION = '3',
    VEGA_LITE_DEFAULT_WIDTH = 400,
    VEGA_LITE_DEFAULT_HEIGHT = 400,
)

def init(app):
    """Perform the configuration of the Flask app.
    Set the defaults, and then read JSON config file."""
    # Set the defaults specified above.
    app.config.from_mapping(CONFIG)
    # Modify the configuration from a JSON config file.
    try:
        filepath = os.environ['CONFIG_FILEPATH']
        app.config.from_json(filepath)
        # Raises an error if filepath variable defined, but no such file.
    except KeyError:
        for filepath in ['config.json', '../site/config.json']:
            filepath = os.path.normpath(os.path.join(ROOT_DIRPATH, filepath))
            try:
                app.config.from_json(filepath)
            except FileNotFoundError:
                filepath = None
            else:
                break
    if filepath:
        print(' > Configuration file:', filepath)
