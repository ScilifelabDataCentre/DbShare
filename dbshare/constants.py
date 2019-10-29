"Constant values."

import re
import string
import sqlite3

import dbshare

# Version numbers not obtainable programmatically
BOOTSTRAP_VERSION        = '4.3.1'
JQUERY_VERSION           = '3.3.1'
JQUERY_LOCALTIME_VERSION = '0.9.1'
DPATH_VERSION            = '1.4.2'
DATATABLES_VERSION       = '1.10.18'
VEGA_VERSION             = '5'
VEGA_LITE_VERSION        = '3'

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
CHARTS  = '_charts'

# Database constants
TABLE   = 'table'
VIEW    = 'view'
INTEGER = 'INTEGER'
REAL    = 'REAL'
TEXT    = 'TEXT'
BLOB    = 'BLOB'
COLUMN_TYPES = (INTEGER, REAL, TEXT, BLOB)

# User roles
ADMIN = 'admin'
USER  = 'user'
USER_ROLES = (ADMIN, USER)

# User statuses
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'
USER_STATUSES = (PENDING, ENABLED, DISABLED)

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
