"Script to create an admin user account."

import sys
import getpass

import flask

import dbshare
import dbshare.app
import dbshare.user
from dbshare import constants

with dbshare.app.app.app_context():
    try:
        with dbshare.user.UserContext() as ctx:
            ctx.set_username(input('username > '))
            ctx.set_email(input('email > '))
            ctx.set_role(constants.ADMIN)
            ctx.set_status(constants.ENABLED)
            ctx.set_password(getpass.getpass('password > '))
    except ValueError as error:
        sys.exit("Error: %s" % error)
    print('Created admin user', ctx.user['username'])
