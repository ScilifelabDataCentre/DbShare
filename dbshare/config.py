"Configuration."

import os
import os.path
import sqlite3

import dbshare
from dbshare import constants


# Default configurable values; modified by reading JSON file in 'init'.
DEFAULT_SETTINGS = dict(
    SERVER_NAME="localhost:5001",  # For URL generation; app.run() in devel.
    REVERSE_PROXY=False,
    DATABASES_DIR="data",
    SITE_NAME="DbShare",
    SITE_STATIC_DIR=None,
    SITE_ICON=None,  # Filename, must be in 'SITE_STATIC_DIR'.
    SITE_LOGO=None,  # Filename, must be in 'SITE_STATIC_DIR'.
    HOST_LOGO=None,  # Filename, must be in 'SITE_STATIC_DIR'.
    HOST_NAME=None,
    HOST_URL=None,
    SECRET_KEY=None,
    SALT_LENGTH=12,
    JSON_AS_ASCII=False,
    JSON_SORT_KEYS=False,
    MIN_PASSWORD_LENGTH=6,
    PERMANENT_SESSION_LIFETIME=7 * 24 * 60 * 60,  # In seconds; = 1 week.
    USER_DEFAULT_QUOTA=2 ** 27,  # = 134 megabytes.
    TABLE_INITIAL_COLUMNS=8,
    MAX_NROWS_DISPLAY=2000,
    CONTENT_HASHES=["md5", "sha1"],
    QUERY_DEFAULT_LIMIT=200,
    DOCUMENTATION_DIR=os.path.join(constants.ROOT, "documentation"),
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
    EXECUTE_TIMEOUT=2.0,
    EXECUTE_TIMEOUT_INCREMENT=0.010,
    EXECUTE_TIMEOUT_BACKOFF=1.75,
    CSV_FILE_DELIMITERS={
        "comma": {"label": "comma ','", "char": ","},
        "tab": {"label": "tab '\\t'", "char": "\t"},
        "semicolon": {"label": "semicolon ';'", "char": ";"},
        "vertical-bar": {"label": "vertical-bar '|'", "char": "|"},
        "colon": {"label": "colon ':'", "char": ":"},
    },
    MARKDOWN_SYNTAX_URL="https://www.markdownguide.org/basic-syntax/",
    ADMIN_USERNAME=None,  # Admin user to create at startup, if not exists.
    ADMIN_EMAIL=None,
    ADMIN_PASSWORD=None,
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
        filepath = os.environ["SETTINGS_FILEPATH"]
        app.config.from_json(filepath)
        # Raises an error if filepath variable defined, but no such file.
    except KeyError:
        for filepath in ["settings.json", "../site/settings.json"]:
            filepath = os.path.normpath(os.path.join(constants.ROOT, filepath))
            try:
                app.config.from_json(filepath)
            except FileNotFoundError:
                filepath = None
            else:
                app.config["SETTINGS_FILEPATH"] = filepath
                break
    app.config["DATABASES_DIR"] = os.path.expanduser(app.config["DATABASES_DIR"])
    app.config["DATABASES_DIR"] = os.path.expandvars(app.config["DATABASES_DIR"])
    # Sanity checks. Exception means bad setup.
    if not app.config["SECRET_KEY"]:
        raise ValueError("SECRET_KEY not set.")
    if app.config["SALT_LENGTH"] <= 6:
        raise ValueError("SALT_LENGTH is too short.")
    if app.config["MIN_PASSWORD_LENGTH"] <= 4:
        raise ValueError("MIN_PASSWORD_LENGTH is too short.")
    if app.config["EXECUTE_TIMEOUT"] <= 0:
        raise ValueError("EXECUTE_TIMEOUT must be positive.")
    if app.config["EXECUTE_TIMEOUT_INCREMENT"] <= 0:
        raise ValueError("EXECUTE_TIMEOUT_INCREMENT must be positive.")
    if app.config["EXECUTE_TIMEOUT_BACKOFF"] <= 1.0:
        raise ValueError("EXECUTE_TIMEOUT_BACKOFF must be greater than 1.")
