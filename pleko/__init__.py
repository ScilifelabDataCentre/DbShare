"Pleko: Experimental web-based toolbench for data handling."

__version__ = '0.5.3'

default_config = dict(
    VERSION = __version__,
    SERVER_NAME = '127.0.0.1:5000',
    SITE_NAME = 'Pleko',
    GITHUB_URL = 'https://github.com/pekrau/Pleko',
    SQLITE_URL = 'https://www.sqlite.org/',
    MASTERDB_FILEPATH = 'data/masterdb.sqlite3',
    DBS_DIRPATH = 'data/dbs',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # Regexp's
    TABLE_INITIAL_COLUMNS = 8,
    QUERY_DEFAULT_LIMIT = 100
)
