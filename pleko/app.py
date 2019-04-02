"Pleko web app."

import json
import sqlite3

import flask
import jinja2.utils

import pleko
import pleko.db
import pleko.index
import pleko.master
import pleko.plot
import pleko.query
import pleko.table
import pleko.user
import pleko.view
from pleko import constants
from pleko import utils

def create_app():
    "Return the configured app object. Initialize the master, if not done."
    app = flask.Flask(__name__)
    app.config.from_mapping(pleko.default_config)
    app.config.from_json('config.json')
    app.config['SQLITE_VERSION'] = sqlite3.sqlite_version
    with open(app.config['VEGA_LITE_SCHEMA']) as infile:
        app.config['VEGA_LITE_SCHEMA'] = json.load(infile)
    app.url_map.converters['name'] = utils.NameConverter
    app.url_map.converters['nameext'] = utils.NameExtConverter
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    pleko.master.init(app)
    utils.mail.init_app(app)
    return app

app = create_app()
app.register_blueprint(pleko.user.blueprint, url_prefix='/user')
app.register_blueprint(pleko.db.blueprint, url_prefix='/db')
app.register_blueprint(pleko.table.blueprint, url_prefix='/table')
app.register_blueprint(pleko.query.blueprint, url_prefix='/query')
app.register_blueprint(pleko.view.blueprint, url_prefix='/view')
app.register_blueprint(pleko.index.blueprint, url_prefix='/index')
app.register_blueprint(pleko.plot.blueprint, url_prefix='/plot')

@app.template_filter('or_null_safe')
def or_null_safe(value):
    "Output None as HTML '<NULL>' in safe mode."
    if value is None:
        return jinja2.utils.Markup('<i>&lt;NULL&gt;</i>')
    else:
        return value

@app.before_request
def prepare():
    "Connect to the master database (read-only); get the current user."
    flask.g.cnx = pleko.master.get_cnx()
    flask.g.current_user = pleko.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == constants.ADMIN

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils,
                len=len,
                enumerate=enumerate)

@app.route('/')
def home():
    "Home page. List accessible databases."
    return flask.render_template('home.html', dbs=pleko.db.get_dbs(public=True))

@app.route('/owner/<name:username>')
@pleko.user.login_required
def owner(username):
    "List of databases owned by the given user."
    if not (flask.g.is_admin or flask.g.current_user['username'] == username):
        flask.flash('you may not access this page')
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('owner.html',
                                 dbs=pleko.db.get_dbs(owner=username),
                                 username=username)

@app.route('/all')
@pleko.user.admin_required
def all():
    "List of all databases."
    dbs = pleko.db.get_dbs()
    usage = sum([db['size'] for db in dbs])
    return flask.render_template('all.html', dbs=dbs, usage=usage)

@app.after_request
def finalize(response):
    try:
        flask.g.cnx.close()
    except AttributeError:
        pass
    try:
        flask.g.dbcnx.close()
    except AttributeError:
        pass
    return response


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
