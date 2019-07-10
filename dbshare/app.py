"DbShare web app."

import json
import time

import flask
import flask_mail

import dbshare
import dbshare.about
import dbshare.config
import dbshare.db
import dbshare.dbs
import dbshare.query
import dbshare.site
import dbshare.system
import dbshare.table
import dbshare.template
import dbshare.templates
import dbshare.user
import dbshare.vega
import dbshare.vega_lite
import dbshare.view
import dbshare.visual

import dbshare.api.root
import dbshare.api.db
import dbshare.api.dbs
import dbshare.api.schema
import dbshare.api.table
import dbshare.api.template
import dbshare.api.templates
import dbshare.api.user
import dbshare.api.users
import dbshare.api.view

from dbshare import constants
from dbshare import utils

app = flask.Flask('dbshare', template_folder='html')
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['nameext'] = utils.NameExtConverter
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Get and sanity check the configuration.
dbshare.config.init(app)
assert app.config['SECRET_KEY']
assert app.config['SALT_LENGTH'] > 6
assert app.config['MIN_PASSWORD_LENGTH'] > 4
assert app.config['EXECUTE_TIMEOUT'] > 0.0
assert app.config['EXECUTE_TIMEOUT_INCREMENT'] > 0.0
assert app.config['EXECUTE_TIMEOUT_BACKOFF'] > 1.0

# Read the JSON Schema files; must be present.
with open(app.config['VEGA_SCHEMA']) as infile:
    app.config['VEGA_SCHEMA'] = json.load(infile)
with open(app.config['VEGA_LITE_SCHEMA']) as infile:
    app.config['VEGA_LITE_SCHEMA'] = json.load(infile)

# Init the system database.
dbshare.system.init(app)

# Init the mail handler.
utils.mail.init_app(app)

# Set up the URL map.
app.register_blueprint(dbshare.db.blueprint, url_prefix='/db')
app.register_blueprint(dbshare.dbs.blueprint, url_prefix='/dbs')
app.register_blueprint(dbshare.table.blueprint, url_prefix='/table')
app.register_blueprint(dbshare.query.blueprint, url_prefix='/query')
app.register_blueprint(dbshare.view.blueprint, url_prefix='/view')
app.register_blueprint(dbshare.visual.blueprint, url_prefix='/visual')
app.register_blueprint(dbshare.template.blueprint, url_prefix='/template')
app.register_blueprint(dbshare.templates.blueprint, url_prefix='/templates')
app.register_blueprint(dbshare.vega.blueprint, url_prefix='/vega')
app.register_blueprint(dbshare.vega_lite.blueprint, url_prefix='/vega-lite')
app.register_blueprint(dbshare.user.blueprint, url_prefix='/user')
app.register_blueprint(dbshare.about.blueprint, url_prefix='/about')
app.register_blueprint(dbshare.site.blueprint, url_prefix='/site')

app.register_blueprint(dbshare.api.root.blueprint, url_prefix='/api')
app.register_blueprint(dbshare.api.db.blueprint, url_prefix='/api/db')
app.register_blueprint(dbshare.api.dbs.blueprint, url_prefix='/api/dbs')
app.register_blueprint(dbshare.api.table.blueprint, url_prefix='/api/table')
app.register_blueprint(dbshare.api.view.blueprint, url_prefix='/api/view')
app.register_blueprint(dbshare.api.template.blueprint,
                       url_prefix='/api/template')
app.register_blueprint(dbshare.api.templates.blueprint,
                       url_prefix='/api/templates')
app.register_blueprint(dbshare.api.user.blueprint, url_prefix='/api/user')
app.register_blueprint(dbshare.api.users.blueprint, url_prefix='/api/users')
app.register_blueprint(dbshare.api.schema.blueprint, url_prefix='/api/schema')

# Add template filters.
app.add_template_filter(utils.thousands)
app.add_template_filter(utils.float3g)
app.add_template_filter(utils.size_none)
app.add_template_filter(utils.none_as_question_mark)
app.add_template_filter(utils.none_as_literal_null)
app.add_template_filter(utils.none_as_empty_string)
app.add_template_filter(utils.do_markdown, name='markdown')
app.add_template_filter(utils.access)
app.add_template_filter(utils.mode)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils,
                enumerate=enumerate,
                len=len,
                range=range,
                round=round,
                is_none=lambda v: v is None)

@app.before_request
def prepare():
    "Connect to the system database (read-only); get the current user."
    flask.g.cnx = dbshare.system.get_cnx()
    flask.g.current_user = dbshare.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == constants.ADMIN
    flask.g.timer = utils.Timer()

@app.route('/')
def home():
    "Home page; display the list of public databases."
    if utils.accept_json():
        return flask.redirect(flask.url_for('api.root'))
    return flask.render_template('home.html',
                                 dbs=dbshare.dbs.get_dbs(public=True))


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
