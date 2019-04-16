"Upload a Pleko Sqlite3 database file into the site."

import argparse
import os.path
import sys

import flask

import pleko
import pleko.app
import pleko.user
from pleko import constants

parser = argparse.ArgumentParser('Upload a Pleko Sqlite3 database file.')
parser.add_argument('username', help='Owner of the uploaded database.')
parser.add_argument('filename', help='Path of the file to upload.')
args = parser.parse_args()

with pleko.app.app.app_context():
    try:
        user = pleko.user.get_user(username=args.username)
        if user is None: raise ValueError('no such user')
        flask.g.current_user = user
        with open(args.filename, 'rb') as infile:
            content = infile.read()
        dbname = os.path.splitext(os.path.basename(args.filename))[0]
        pleko.db.add_database(dbname, None, content)
    except (ValueError, IOError) as error:
        sys.exit("Error: %s" % error)
    print('Uploaded database', dbname)
