"Script to create an admin user account."

import sys

import flask

import pleko
import pleko.app
import pleko.constants
import pleko.user
import pleko.utils

app = pleko.app.create_app()

with app.app_context():
    db = pleko.user.userdb.UserDb(app.config)

    username = input('username > ')
    if not username:
        sys.exit('Error: no username given')
    email = input('email > ')
    if not email:
        sys.exit('Error: no email given')

    try:
        user = db.create(username, email, pleko.constants.ADMIN, 
                         status=pleko.constants.ENABLED)
    except ValueError as error:
        sys.exit("Error: %s" % error)
    else:
        print('Created admin user', username)
        query = dict(username=user['username'],
                     code=user['password'][len('code:'):])
        url = pleko.utils.get_absolute_url('user.password', query=query)
        print('To set password, go to', url)
