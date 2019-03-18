"Constant values."

import re

IDENTIFIER_RX = re.compile(r'^[a-z][a-z0-9_]*$', re.I)
EMAIL_RX      = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

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
COLUMN_TYPES = ('INTEGER', 'REAL', 'TEXT', 'BLOB')
