"Upload a CSV file into a pre-existing DbPortal database."

import argparse
import os.path
import sys

import flask

import dbportal
import dbportal.app
import dbportal.db
import dbportal.user
from dbportal import constants
from dbportal import utils

with dbportal.app.app.app_context():
    delimiters = flask.current_app.config['CSV_FILE_DELIMITERS']
    parser = argparse.ArgumentParser('Upload a CSV file as a table'
                                     ' into a DbPortal database.')
    parser.add_argument('dbname', help='Name of the database.')
    parser.add_argument('filename', help='Path of the CSV file to upload.')
    parser.add_argument('--delimiter', default='comma',
                        choices=list(delimiters.keys()),
                        help='The delimiter character between items in a line.')
    parser.add_argument('--nullrepr', default='', action='store',
                        help='The string used to represent the NULL value'
                        ' in the CSV file records.')
    parser.add_argument('--noheader', dest='header', action='store_false',
                        help='The CSV file contains no header record.')
    args = parser.parse_args()
    try:
        db = dbportal.db.get_db(args.dbname, complete=True)
        if db is None: raise ValueError('no such database')
        flask.g.current_user = dbportal.user.get_user(username=db['owner'])
        tablename = os.path.basename(args.filename)
        tablename = os.path.splitext(tablename)[0]
        delimiter = delimiters[args.delimiter]['char']
        with open(args.filename, newline='') as infile:
            with dbportal.db.DbContext(db) as ctx:
                tablename, n = ctx.load_csvfile(infile, tablename,
                                                delimiter=delimiter,
                                                nullrepr=args.nullrepr,
                                                header=args.header)
    except (ValueError, IOError) as error:
        sys.exit(f"Error: {str(error)}")
    print(f"Loaded {n} records into table {tablename} in database {args.dbname}.")
