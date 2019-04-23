"Upload a DbPortal Sqlite3 database file into the site."

import argparse
import os.path
import sys

import flask

import dbportal
import dbportal.app
import dbportal.user
from dbportal import constants

parser = argparse.ArgumentParser('Upload a DbPortal Sqlite3 database file.')
parser.add_argument('username', help='Owner of the uploaded database.')
parser.add_argument('filename', help='Path of the file to upload.')
args = parser.parse_args()

with dbportal.app.app.app_context():
    try:
        user = dbportal.user.get_user(username=args.username)
        if user is None: raise ValueError('no such user')
        flask.g.current_user = user
        with open(args.filename, 'rb') as infile:
            content = infile.read()
        dbname = os.path.splitext(os.path.basename(args.filename))[0]
        dbportal.db.add_database(dbname, None, content)
    except (ValueError, IOError) as error:
        sys.exit("Error: %s" % error)
    print('Uploaded database', dbname)
