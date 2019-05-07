"Database lists endpoints."

import os.path

import flask

import dbportal.db
import dbportal.user

from dbportal import utils


blueprint = flask.Blueprint('dbs', __name__)
api_blueprint = flask.Blueprint('api_dbs', __name__)

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
        return flask.redirect(flask.url_for('db.home', dbname=db['name']))

@blueprint.route('/public')
def public():
    "Display the list of public databases."
    return flask.render_template('dbs/public.html',
                                 dbs=dbportal.db.get_dbs(public=True))

@api_blueprint.route('/public')
def api_public():
    "Return the list of public databases."
    dbs = dbportal.db.get_dbs(public=True)
    result = utils.get_api(title='Public databases',
                           databases=get_api_dbs(dbs))
    return flask.jsonify(result)
                 

@blueprint.route('/all')
@dbportal.user.admin_required
def all():
    "Display the list of all databases."
    dbs = dbportal.db.get_dbs()
    return flask.render_template('dbs/all.html',
                                 dbs=dbs,
                                 total_size=sum([db['size'] for db in dbs]))

@api_blueprint.route('/all')
@dbportal.user.admin_required
def api_all():
    "Return the list of all databases."
    dbs = dbportal.db.get_dbs()
    return flask.jsonify(
        utils.get_api(title='All databases',
                      total_size=sum([db['size'] for db in dbs]),
                      databases=get_api_dbs(dbs)))

@blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def owner(username):
    "Display the list of databases owned by the given user."
    if not access(username):
        flask.flash("you may not access the list of the user's databases")
        return flask.redirect(flask.url_for('home'))
    dbs = dbportal.db.get_dbs(owner=username)
    return flask.render_template('dbs/owner.html',
                                 dbs=dbs,
                                 total_size=sum([db['size'] for db in dbs]),
                                 username=username)

@api_blueprint.route('/owner/<name:username>')
@dbportal.user.login_required
def api_owner(username):
    "Return the list of databases owned by the given user."
    if not access(username):
        return flask.abort(401)
    dbs = dbportal.db.get_dbs(owner=username)
    result = utils.get_api(title="User's databases",
                           total_size=sum([db['size'] for db in dbs]),
                           databases=get_api_dbs(dbs))
    result['links']['user'] = utils.url_for('api_user.api_profile',
                                            username=username)
    return flask.jsonify(result)

def access(username):
    "May the current user access the user's list of databases?"
    return flask.g.is_admin or flask.g.current_user['username'] == username

def get_api_dbs(dbs):
    "Return a JSON-formatted databases list."
    return [{'name': db['name'],
             'title': db.get('title'),
             'owner': db['owner'],
             'public': db['public'],
             'readonly': db['readonly'],
             'size': db['size'],
             'modified': db['modified'],
             'href': utils.url_for('api_db.api_home', dbname=db['name'])}
            for db in dbs]
