"Database lists HTML endpoints."

import os.path

import flask

import dbshare.db

from . import utils


blueprint = flask.Blueprint('dbs', __name__)

@blueprint.route('/upload', methods=['GET', 'POST'])
@utils.login_required
def upload():
    "Upload a database file: Sqlite3 or XLSX file."
    if utils.http_GET():
        return flask.render_template('dbs/upload.html')

    elif utils.http_POST():
        try:
            infile = flask.request.files.get('sqlite3file')
            if infile is None:
                infile = flask.request.files.get('xlsxfile')
                if infile is None:
                    raise ValueError('no file given')
                else:
                    add_func = dbshare.db.add_xlsx_database
            else:
                add_func = dbshare.db.add_sqlite3_database
            dbname = flask.request.form.get('dbname')
            if not dbname:
                dbname = os.path.splitext(os.path.basename(infile.filename))[0]
            db = add_func(dbname, infile, infile.content_length)
        except ValueError as error:
            utils.flash_error(error)
            return flask.redirect(flask.url_for('.upload'))
        return flask.redirect(flask.url_for('db.display', dbname=db['name']))

@blueprint.route('/public')
def public():
    "Display the list of public databases."
    return flask.render_template('dbs/public.html',
                                 dbs=get_dbs(public=True))

@blueprint.route('/all')
@utils.admin_required
def all():
    "Display the list of all databases."
    dbs = get_dbs()
    return flask.render_template('dbs/all.html',
                                 dbs=dbs,
                                 total_size=sum([db['size'] for db in dbs]))

@blueprint.route('/owner')
@blueprint.route('/owner/<name:username>')
@utils.login_required
def owner(username=''):
    "Display the list of databases owned by the given user."
    if not username:
        username = flask.g.current_user['username']
    elif not has_access(username):
        utils.flash_error("you may not access the list of the user's databases")
        return flask.redirect(flask.url_for('home'))
    dbs = get_dbs(owner=username)
    return flask.render_template('dbs/owner.html',
                                 dbs=dbs,
                                 total_size=sum([db['size'] for db in dbs]),
                                 username=username)

@blueprint.route('/lookup/<hashcode>')
def lookup(hashcode):
    "Lookup and redirect to the database with the given hash."
    for db in get_dbs(readonly=True):
        for hashvalue in db['hashes'].values():
            if hashvalue == hashcode:
                return flask.redirect(
                    flask.url_for('db.display', dbname=db['name']))
    utils.flash_error('no such database')
    return flask.redirect(flask.url_for('home'))

def has_access(username):
    "May the current user access the user's list of databases?"
    return flask.g.is_admin or flask.g.current_user['username'] == username

def get_dbs(public=None, owner=None, complete=False, readonly=None):
    "Get the list of databases according to criteria."
    sql = "SELECT name FROM dbs"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if readonly is not None:
        criteria['readonly=?'] = readonly
    if criteria:
        sql += ' WHERE ' + ' OR '.join(criteria.keys())
    cursor = dbshare.system.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [dbshare.db.get_db(row[0], complete=complete) for row in cursor]
