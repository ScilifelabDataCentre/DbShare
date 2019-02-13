"Pleko: Experimental web-based toolbench for data handling."

__version__ = '0.1.0'


class DefaultConfig:
    VERSION = __version__
    SITE_NAME = 'Pleko'
    GITHUB_URL = 'https://github.com/pekrau/Pleko'
    FLASK_DEBUG = False
    LOGGING_DEBUG = False
    SECRET_KEY = None
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60
    USER_DBI = {}
    JSON_INDENT = None
    CONTACT_EMAIL = None
    EMAIL = {}
    USER_EMAIL_AUTOENABLE = []
