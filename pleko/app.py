"Pleko web app."

import sqlite3

import flask
import jinja2.utils

import pleko
import pleko.db
import pleko.index
import pleko.master
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
    app.url_map.converters['iuid'] = utils.IuidConverter
    app.url_map.converters['name'] = utils.NameConverter
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


@app.template_filter('or_null_safe')
def or_null_safe(value):
    "Output None as HTML '<NULL>' in safe mode."
    if value is None:
        return jinja2.utils.Markup('<i>&lt;NULL&gt;</i>')
    else:
        return value

@app.before_request
def prepare():
    "Connect to the master database; get the current user."
    flask.g.cnx = pleko.master.get_cnx()
    flask.g.dbcnx = {}
    flask.g.current_user = pleko.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == constants.ADMIN


@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils)

@app.route('/')
def home():
    "Home page. List accessible databases."
    dbs = pleko.db.get_dbs(public=not flask.g.is_admin)
    return flask.render_template('home.html', dbs=dbs)

@app.after_request
def finalize(response):
    flask.g.cnx.close()
    for dbcnx in flask.g.dbcnx.values():
        dbcnx.close()
    return response


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
