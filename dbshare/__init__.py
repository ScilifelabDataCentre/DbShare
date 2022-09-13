"DbShare: Web service to share and query data stored in SQLite3 databases."

import json
import os.path
import re
import string

__version__ = "2.7.2"


class Constants:
    VERSION = __version__
    URL = "https://github.com/pekrau/DbShare"
    ROOT = os.path.dirname(os.path.abspath(__file__))

    BOOTSTRAP_VERSION = "4.6.2"
    BOOTSTRAP_URL = "https://getbootstrap.com/"
    BOOTSTRAP_CSS_URL = (
        "https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css"
    )
    BOOTSTRAP_CSS_INTEGRITY = (
        "sha384-xOolHFLEh07PJGoPkLv1IbcEPTNtaed2xpHsD9ESMhqIYd0nLMwNLD69Npy4HI+N"
    )
    BOOTSTRAP_JS_URL = (
        "https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"
    )
    BOOTSTRAP_JS_INTEGRITY = (
        "sha384-Fy6S3B9q64WdZWQUiU+q4/2Lc9npb8tCaSX9FK7E8HnRr0Jz8D6OP9dO5Vg3Q9ct"
    )

    JQUERY_VERSION = "3.5.1"
    JQUERY_URL = "https://jquery.com/"
    JQUERY_JS_URL = "https://code.jquery.com/jquery-3.5.1.slim.min.js"
    JQUERY_JS_INTEGRITY = (
        "sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj"
    )

    JQUERY_LOCALTIME_URL = "https://plugins.jquery.com/jquery.localtime/"
    JQUERY_LOCALTIME_VERSION = "0.9.1"
    JQUERY_LOCALTIME_FILENAME = "jquery.localtime-0.9.1.min.js"

    DATATABLES_VERSION = "1.10.24"
    DATATABLES_URL = "https://datatables.net/"
    DATATABLES_CSS_URL = (
        "https://cdn.datatables.net/1.10.24/css/dataTables.bootstrap4.min.css"
    )
    DATATABLES_JQUERY_JS_URL = (
        "https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js"
    )
    DATATABLES_BOOTSTRAP_JS_URL = (
        "https://cdn.datatables.net/1.10.24/js/dataTables.bootstrap4.min.js"
    )

    DPATH_URL = "https://github.com/akesterson/dpath-python"
    DPATH_VERSION = "1.4.2"

    NAME_RX = re.compile(r"^[a-z][a-z0-9_-]*$", re.I)
    NAME_CHARS = frozenset(string.ascii_letters + string.digits + "_" + "-")
    NAME_EXT_RX = re.compile(r"^([a-z][a-z0-9_-]*)(\.[a-z0-9_\.-]+)?$", re.I)
    EMAIL_RX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    # System database name.
    SYSTEM = "_system"

    # Meta table names in each database.
    TABLES = "_tables"
    INDEXES = "_indexes"
    VIEWS = "_views"

    # Database constants.
    TABLE = "table"
    VIEW = "view"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"
    COLUMN_TYPES = (INTEGER, REAL, TEXT, BLOB)

    # User roles.
    ADMIN = "admin"
    USER = "user"
    USER_ROLES = (ADMIN, USER)

    # User statuses.
    PENDING = "pending"
    ENABLED = "enabled"
    DISABLED = "disabled"
    USER_STATUSES = (PENDING, ENABLED, DISABLED)

    # MIME types.
    HTML_MIMETYPE = "text/html"
    CSV_MIMETYPE = "text/csv"
    JSON_MIMETYPE = "application/json"
    SQLITE3_MIMETYPE = "application/x-sqlite3"
    TAR_MIMETYPE = "application/x-tar"
    XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Miscellaneous.
    FRONT_MATTER_RX = re.compile(r"^---(.*)---", re.DOTALL | re.MULTILINE)

    def __setattr__(self, key, value):
        raise ValueError("cannot set constant")


constants = Constants()
