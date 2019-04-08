"""Pleko
Explore, visualize and publish data sets with Sqlite3 and Vega-Lite.
"""

import os.path

__version__ = '0.8.2'

ROOT_DIR = os.path.dirname(__file__)

default_config = dict(
    VERSION = __version__,
    SERVER_NAME = '127.0.0.1:5000',
    SITE_NAME = 'Pleko',
    GITHUB_URL = 'https://github.com/pekrau/Pleko',
    FLASK_URL = 'http://flask.pocoo.org/',
    SQLITE_URL = 'https://www.sqlite.org/',
    BOOTSTRAP_URL = 'https://getbootstrap.com/docs/4.3/getting-started/introduction/',
    VEGA_LITE_URL = 'https://vega.github.io/vega-lite/',
    VEGA_LITE_SCHEMA = os.path.join(ROOT_DIR, 'static/vega-lite-v3.json'),
    DATABASES_DIRPATH = 'data',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    JSONIFY_AS_ASCII = False,
    JSON_SORT_KEYS = False,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # Regexp's
    USER_DEFAULT_QUOTA = 2**22,       # 4 megabyte
    TABLE_INITIAL_COLUMNS = 8,
    QUERY_DEFAULT_LIMIT = 100
)
