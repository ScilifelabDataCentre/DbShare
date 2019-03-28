"Constant values."

import re

NAME_RX      = re.compile(r'^[a-z][a-z0-9_]*$', re.I)
NAME_EXT_RX  = re.compile(r'^([a-z][a-z0-9_]*)(\.[a-z0-9_]+)?$', re.I)
EMAIL_RX     = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

EXTS = frozenset([None, 'html', 'csv', 'json'])

INDEX_PREFIX_TEMPLATE = "%s$index"

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
INTEGER = 'INTEGER'
REAL    = 'REAL'
TEXT    = 'TEXT'
BLOB    = 'BLOB'
COLUMN_TYPES = (INTEGER, REAL, TEXT, BLOB)

# MIME types
CSV_MIMETYPE  = 'text/csv'
JSON_MIMETYPE = 'application/json'
