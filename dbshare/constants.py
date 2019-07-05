"Constant values."

import re
import string


NAME_RX      = re.compile(r'^[a-z][a-z0-9_-]*$', re.I)
NAME_CHARS   = frozenset(string.ascii_letters + string.digits + '_' + '-')
NAME_EXT_RX  = re.compile(r'^([a-z][a-z0-9_-]*)(\.[a-z0-9_\.]+)?$', re.I)
EMAIL_RX     = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

# System database name
SYSTEM  = '_system'

# Meta table names in each database
TABLES  = '_tables'
INDEXES = '_indexes'
VIEWS   = '_views'
VISUALS = '_visuals'

# Template types
VEGA_LITE = 'Vega-Lite'
VEGA      = 'Vega'
TEMPLATE_TYPES = (VEGA_LITE, VEGA)

# User roles
ADMIN = 'admin'
USER  = 'user'
USER_ROLES = (ADMIN, USER)

# User statuses
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'
USER_STATUSES = (PENDING, ENABLED, DISABLED)

# Database constants
TABLE   = 'table'
VIEW    = 'view'
INTEGER = 'INTEGER'
REAL    = 'REAL'
TEXT    = 'TEXT'
BLOB    = 'BLOB'
COLUMN_TYPES = (INTEGER, REAL, TEXT, BLOB)

# MIME types
HTML_MIMETYPE    = 'text/html'
CSV_MIMETYPE     = 'text/csv'
JSON_MIMETYPE    = 'application/json'
SQLITE3_MIMETYPE = 'application/x-sqlite3'
TAR_MIMETYPE     = 'application/x-tar'
XLSX_MIMETYPE    = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

# JSON schema
SCHEMA_BASE_URL = 'https://dbshare.scilifelab.se/api/schema'
SCHEMA_SCHEMA_URL = 'http://json-schema.org/draft-07/schema#'
