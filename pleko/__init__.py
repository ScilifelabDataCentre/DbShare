"Pleko: Experimental web-based toolbench for data handling."

__version__ = '0.4.2'

default_config = dict(
    VERSION = __version__,
    SERVER_NAME = '127.0.0.1:5000',
    SITE_NAME = 'Pleko',
    GITHUB_URL = 'https://github.com/pekrau/Pleko',
    MASTERDB_FILEPATH = 'masterdb.sqlite3',
    RELDB_DIRPATH = 'reldb',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # Regexp's
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60 # seconds; 1 week
)
