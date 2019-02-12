"Settings. Load site-specific values from 'settings.json' or env vars."

import logging
import json
import os

import pleko

SITE_NAME = 'Pleko'
LOGGING_DEBUG = False
FLASK_DEBUG = False
JSON_INDENT = None
PREFERRED_URL_SCHEME = None
SERVER_NAME = None
CONTACT_EMAIL = None
EMAIL = {}
USER_EMAIL_AUTOENABLE = []

# Constant random string at least 16 chars long; must be set by 'load'.
SECRET_KEY = None

# Constant random string at least 16 chars long; must be set by 'load'.
HASH_SALT  = None

# User database interface settings; must be set by 'load'.
USER_DBI = {}

# Login session duration, in seconds.
MAX_SESSION_AGE = 7 * 24 * 60 * 60


def load(filepath='settings.json'):
    """Load the site-specific settings from the given JSON file or env vars.
    Values from env vars override those in the JSON file.
    """
    g = globals()
    try:
        with open(filepath, 'r') as infile:
            for key, value in json.load(infile).items():
                g[key] = value
    except OSError:
        pass
    prefix = 'PLEKO_'
    for key, value in os.environ.items():
        if key.startswith(prefix):
            g[key[len(prefix):]] = value
    if not USER_DBI:
        raise ValueError('no user database interface settings')
    if not SECRET_KEY or len(SECRET_KEY) < 16:
        raise ValueError('SECRET_KEY not defined, or too short')
    if not HASH_SALT or len(HASH_SALT) < 16:
        raise ValueError('HASH_SALT not defined, or too short')
    if LOGGING_DEBUG:
        kwargs = dict(level=logging.DEBUG)
    else:
        kwargs = dict(level=logging.INFO)
    logging.basicConfig(**kwargs)
    logging.info("Pleko version %s", pleko.__version__)
    logging.debug('logging debug')
    
