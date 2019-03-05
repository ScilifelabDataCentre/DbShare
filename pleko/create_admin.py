"Script to create an admin user account."

import sys
import getpass

import flask

import pleko
import pleko.app
import pleko.constants
import pleko.user
import pleko.userdb

app = pleko.app.create_app()
with app.app_context():
    userdb = pleko.user.userdb.UserDb(app.config)
    try:
        with userdb.get_context() as ctx:
            ctx.set_username(input('username > '))
            ctx.set_email(input('email > '))
            ctx.set_role(pleko.constants.ADMIN)
            ctx.set_status(pleko.constants.ENABLED)
            ctx.set_password(getpass.getpass('password > '))
    except ValueError as error:
        sys.exit("Error: %s" % error)
    print('Created admin user', ctx.user['username'])
