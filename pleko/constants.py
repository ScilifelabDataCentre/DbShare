"Constant values."

import re

PLEKO_URL  = 'http://pleko.org/'
GITHUB_URL = 'https://github.com/pekrau/Pleko'

IUID_RX       = re.compile(r'^[a-f0-9]{32,32}$')
IDENTIFIER_RX = re.compile(r'^[a-z][a-z0-9_]*$', re.I)

JSON_MIMETYPE = 'application/json'
HTML_MIMETYPE = 'text/html'

# User statuses and roles
ENABLED = 'enabled'
DISABLED = 'disabled'
USER_STATUSES = (ENABLED, DISABLED)
ADMIN     = 'admin'
USER      = 'user'
USER_ROLES = (ADMIN, USER)
