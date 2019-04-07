"Constant values."

import re
import string

NAME_RX      = re.compile(r'^[a-z][a-z0-9_]*$', re.I)
NAME_CHARS   = frozenset(string.ascii_letters + string.digits + '_')
NAME_EXT_RX  = re.compile(r'^([a-z][a-z0-9_]*)(\.[a-z0-9_]+)?$', re.I)
EMAIL_RX     = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

# Meta database and table names
MASTER     = '_master'
TABLES     = '_tables'
INDEXES    = '_indexes'
VIEWS      = '_views'
PLOTS      = '_plots'
INDEX_PREFIX_TEMPLATE = "_index_%s_"

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
CSV_MIMETYPE  = 'text/csv'
JSON_MIMETYPE = 'application/json'
