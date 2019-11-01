"Configuration."

import os
import os.path
import sqlite3

import dbshare

from . import constants


# Default configurable values; modified by reading JSON file in 'init'.
DEFAULT_SETTINGS = dict(
    SERVER_NAME = '127.0.0.1:5000',
    DATABASES_DIRPATH = 'data',
    SITE_NAME = 'DbShare',
    SITE_STATIC_DIRPATH = None,
    SITE_CHART_TEMPLATES_DIRPATH = None,
    LOG_ACCESS = False,
    HOST_LOGO = None,           # Filename, must be in 'SITE_STATIC_DIRPATH'
    HOST_NAME = None,
    HOST_URL = None,
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    JSON_AS_ASCII = False,
    JSON_SORT_KEYS = False,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # in seconds; 1 week
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # List of regexp's
    USER_DEFAULT_QUOTA = 2**27,       # 134 megabytes
    TABLE_INITIAL_COLUMNS = 8,
    MAX_NROWS_DISPLAY = 2000,
    CONTENT_HASHES = ['md5', 'sha1'],
    QUERY_DEFAULT_LIMIT = 200,
    DOCS_DIRPATH = os.path.join(constants.ROOT_DIRPATH, 'docs'),
    CHART_TEMPLATES_DIRPATH = os.path.join(constants.ROOT_DIRPATH,
                                           'chart_templates'),
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
    MARKDOWN_SYNTAX_URL = 'https://daringfireball.net/projects/markdown/syntax',
    VEGA_LITE_DEFAULT_WIDTH = 400,
    VEGA_LITE_DEFAULT_HEIGHT = 400,
)

def init(app):
    """Configure the Flask app.
    Read a JSON config file to modify the defaults.
    Perform a sanity check on the settings.
    """
    # Set the defaults specified above.
    app.config.from_mapping(DEFAULT_SETTINGS)
    # Modify the configuration as specified in a JSON settings file.
    try:
        filepath = os.environ['SETTINGS_FILEPATH']
        app.config.from_json(filepath)
        # Raises an error if filepath variable defined, but no such file.
    except KeyError:
        for filepath in ['settings.json', '../site/settings.json']:
            filepath = os.path.normpath(os.path.join(constants.ROOT_DIRPATH,
                                                     filepath))
            try:
                app.config.from_json(filepath)
            except FileNotFoundError:
                filepath = None
            else:
                app.config['SETTINGS_FILEPATH'] = filepath
                break
    assert app.config['SECRET_KEY']
    assert app.config['SALT_LENGTH'] > 6
    assert app.config['MIN_PASSWORD_LENGTH'] > 4
    assert app.config['EXECUTE_TIMEOUT'] > 0.0
    assert app.config['EXECUTE_TIMEOUT_INCREMENT'] > 0.0
    assert app.config['EXECUTE_TIMEOUT_BACKOFF'] > 1.0
