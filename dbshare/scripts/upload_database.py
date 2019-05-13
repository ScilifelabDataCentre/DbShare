"Upload a DbShare Sqlite3 database file into the site."

import argparse
import os.path
import sys

import flask

import dbshare
import dbshare.app
import dbshare.user
from dbshare import constants

with dbshare.app.app.app_context():
    parser = argparse.ArgumentParser('Upload a DbShare Sqlite3 database file.')
    parser.add_argument('username', help='Owner of the uploaded database.')
    parser.add_argument('filename', help='Path of the file to upload.')
    args = parser.parse_args()
    try:
        user = dbshare.user.get_user(username=args.username)
        if user is None: raise ValueError('no such user')
        flask.g.current_user = user
        with open(args.filename, 'rb') as infile:
            content = infile.read()
        dbname = os.path.splitext(os.path.basename(args.filename))[0]
        dbshare.db.add_database(dbname, None, content)
    except (ValueError, IOError) as error:
        sys.exit(f"Error: {str(error)}")
    print(f"Uploaded database {dbname}.")
