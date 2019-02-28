"Constant values."

import re

EMAIL_RX      = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
IUID_RX       = re.compile(r'^[a-f0-9]{32,32}$')
IDENTIFIER_RX = re.compile(r'^[a-z][a-z0-9_]*$', re.I)

# Entity types
USER = 'user'
LOG  = 'log'

# User statuses and roles
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'
USER_STATUSES = (PENDING, ENABLED, DISABLED)

ADMIN     = 'admin'
# USER defined above
USER_ROLES = (ADMIN, USER)
