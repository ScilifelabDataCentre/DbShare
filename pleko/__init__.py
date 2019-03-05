"Pleko: Experimental web-based toolbench for data handling."

__version__ = '0.2.5'

default_config = dict(
    VERSION = __version__,
    SERVER_NAME = '127.0.0.1:5000',
    SITE_NAME = 'Pleko',
    GITHUB_URL = 'https://github.com/pekrau/Pleko',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    REGISTRATION_DIRECT = False,
    REGISTRATION_REGEXP_WHITELIST = [],
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60 # seconds; 1 week
)
