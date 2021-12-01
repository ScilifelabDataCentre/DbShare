"Upload a CSV file into a pre-existing DbShare database."

import argparse
import os.path
import sys

import flask

import dbshare
import dbshare.app
import dbshare.db
import dbshare.user
from dbshare import constants
from dbshare import utils

with dbshare.app.app.app_context():
    delimiters = flask.current_app.config['CSV_FILE_DELIMITERS']
    parser = argparse.ArgumentParser('Upload a CSV file as a table'
                                     ' into a DbShare database.')
    parser.add_argument('dbname', help='Name of the database.')
    parser.add_argument('filename', help='Path of the CSV file to upload.')
    parser.add_argument('--delimiter', default='comma',
                        choices=list(delimiters.keys()),
                        help='The delimiter character between items in a line.')
    parser.add_argument('--noheader', dest='header', action='store_false',
                        help='The CSV file contains no header record.')
    args = parser.parse_args()
    try:
        db = dbshare.db.get_db(args.dbname, complete=True)
        if db is None: raise ValueError('no such database')
        flask.g.current_user = dbshare.user.get_user(username=db['owner'])
        tablename = os.path.basename(args.filename)
        tablename = os.path.splitext(tablename)[0]
        tablename = utils.name_cleaned(tablename)
        if utils.name_in_nocase(tablename, db['tables']):
            raise ValueError('table name already in use')
        delimiter = delimiters[args.delimiter]['char']
        # Read the file; eliminate empty records.
        records = [r for r in csv.reader(infile, delimiter=delimiter) if r]
        if not records:
            raise ValueError('empty CSV file')
        # Change empty string items to None.
        for record in records:
            for i, item in enumerate(record):
                if item == '':
                    record[i] = None
        with open(args.filename, newline='') as infile:
            with dbshare.db.DbSaver(db) as saver:
                saver.create_table_load_records(tablename,
                                                records,
                                                has_header=args.header)
    except (ValueError, IOError) as error:
        sys.exit(f"Error: {str(error)}")
    print(f"Loaded {len(records)} records into table {tablename}"
          f" in database {args.dbname}.")
