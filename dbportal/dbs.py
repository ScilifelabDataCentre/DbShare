"Database lists HTML endpoints."

import os.path

import flask

import dbportal.db
import dbportal.user

from dbportal import utils


blueprint = flask.Blueprint('dbs', __name__)

@blueprint.route('/upload', methods=['GET', 'POST'])
@dbportal.user.login_required
def upload():
    "Upload a DbPortal Sqlite3 database file."
    if utils.http_GET():
        return flask.render_template('dbs/upload.html')

    elif utils.http_POST():
        try:
            infile = flask.request.files.get('sqlite3file')
            if infile is None:
                raise ValueError('no file given')
            dbname = flask.request.form.get('dbname')
            if not dbname:
                dbname = os.path.splitext(os.path.basename(infile.filename))[0]
            db = dbportal.db.add_database(dbname, infile, modify_dbname=True)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('.upload'))
        return flask.redirect(flask.url_for('db.display', dbname=db['name']))

@blueprint.route('/public')
def public():
    "Display the list of public databases."
    return flask.render_template('dbs/public.html',
                                 dbs=dbportal.db.get_dbs(public=True))

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Display the list of all databases."
    dbs = dbportal.db.get_dbs()
    return flask.render_template('dbs/all.html',
                                 dbs=dbs,
                                 total_size=sum([db['size'] for db in dbs]))

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Display the list of databases owned by the given user."
    if not has_access(username):
        flask.flash("you may not access the list of the user's databases")
        return flask.redirect(flask.url_for('home'))
    dbs = dbportal.db.get_dbs(owner=username)
    return flask.render_template('dbs/owner.html',
                                 dbs=dbs,
                                 total_size=sum([db['size'] for db in dbs]),
                                 username=username)

def has_access(username):
    "May the current user access the user's list of databases?"
    return flask.g.is_admin or flask.g.current_user['username'] == username

def get_dbs(public=None, owner=None, complete=False):
    "Get the list of databases according to criteria."
    sql = "SELECT name FROM dbs"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' OR '.join(criteria.keys())
    cursor = dbportal.system.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [dbportal.db.get_db(row[0], complete=complete) for row in cursor]
