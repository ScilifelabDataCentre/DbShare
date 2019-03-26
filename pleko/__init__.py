"Pleko: Web-based relational database system powered by Sqlite3."

__version__ = '0.6.4'

default_config = dict(
    VERSION = __version__,
    SERVER_NAME = '127.0.0.1:5000',
    SITE_NAME = 'Pleko',
    GITHUB_URL = 'https://github.com/pekrau/Pleko',
    FLASK_URL = 'http://flask.pocoo.org/',
    SQLITE_URL = 'https://www.sqlite.org/',
    BOOTSTRAP_URL = 'https://getbootstrap.com/docs/4.3/getting-started/introduction/',
    DATABASES_DIRPATH = 'data',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # Regexp's
    TABLE_INITIAL_COLUMNS = 8,
    QUERY_DEFAULT_LIMIT = 100
)
