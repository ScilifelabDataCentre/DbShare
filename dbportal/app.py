"DbPortal web app."

import json
import os
import os.path
import sqlite3

import flask
import flask_mail
import jinja2.utils
import jsonschema

import dbportal
import dbportal.about
import dbportal.db
import dbportal.dbs
import dbportal.index
import dbportal.system
import dbportal.query
import dbportal.table
import dbportal.template
import dbportal.templates
import dbportal.user
import dbportal.vega
import dbportal.vega_lite
import dbportal.view
import dbportal.visual

import dbportal.api_db
import dbportal.api_dbs
import dbportal.api_schema
import dbportal.api_table
import dbportal.api_template
import dbportal.api_templates
import dbportal.api_user

from dbportal import constants
from dbportal import utils

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurable values; the file 'config.json' is read to change these.
CONFIG = dict(
    VERSION = dbportal.__version__,
    SERVER_NAME = '127.0.0.1:5000',
    SITE_NAME = 'DbPortal',
    DATABASES_DIRPATH = 'data',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    JSONIFY_AS_ASCII = False,
    JSON_SORT_KEYS = False,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # List of regexp's
    USER_DEFAULT_QUOTA = 2**22,       # 4 megabyte
    TABLE_INITIAL_COLUMNS = 8,
    MAX_NROWS_DISPLAY = 2000,
    QUERY_DEFAULT_LIMIT = 200,
    # Suggested values for timeout, increment and backoff:
    # t=2.0, i=0.010, b=1.75
    #        i=0.014, b=1.55
    #        i=0.022, b=1.55
    # t=3.0, i=0.012, b=1.50
    #        i=0.014, b=1.95
    #        i=0.022, b=1.80
    # t=4.0, i=0.010, b=1.45
    #        i=0.014, b=1.70
    #        i=0.020, b=1.75
    EXECUTE_TIMEOUT = 2.0,
    EXECUTE_TIMEOUT_INCREMENT = 0.010,
    EXECUTE_TIMEOUT_BACKOFF = 1.75,
    CSV_FILE_DELIMITERS = {'comma': {'label': "comma ','", 'char': ','},
                           'tab': {'label': "tab '\\t'", 'char': '\t'},
                           'semicolon': {'label': "semicolon ';'", 'char': ';'},
                           'vertical-bar': {'label': "vertical-bar '|'", 
                                            'char': '|'},
                           'colon': {'label': "colon ':'", 'char': ':'}},
    DBPORTAL_URL = 'https://github.com/pekrau/DbPortal',
    FLASK_URL = 'http://flask.pocoo.org/',
    JINJA2_URL = 'http://jinja.pocoo.org/docs',
    SQLITE3_URL = 'https://www.sqlite.org/',
    JSONSCHEMA_URL = 'http://json-schema.org/draft-07/schema#',
    # Bootstrap 4.3.1
    BOOTSTRAP_SITE_URL = 'https://getbootstrap.com/docs/4.3/getting-started/introduction/',
    BOOTSTRAP_VERSION = '4.3.1',
    BOOTSTRAP_CSS_ATTRS = 'href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous"',
    JQUERY_SITE_URL = 'https://jquery.com/',
    JQUERY_VERSION = '3.3.1',
    JQUERY_JS_ATTRS = 'src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"',
    POPPER_JS_ATTRS = 'src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"',
    BOOTSTRAP_JS_ATTRS = 'src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"',
    # DataTables 1.10.18 for bootstrap 4
    DATATABLES_CSS_URL = 'https://cdn.datatables.net/1.10.18/css/dataTables.bootstrap4.min.css',
    DATATABLES_JS_URL = 'https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js',
    DATATABLES_BOOTSTRAP_JS_URL = 'https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js',
    DATATABLES_SITE_URL = 'https://datatables.net/',
    DATATABLES_VERSION = '1.10.18',
    # Vega and Vega-Lite
    VEGA_JS_URL = 'https://cdn.jsdelivr.net/npm/vega@5',
    VEGA_SCHEMA_URL = 'https://vega.github.io/schema/vega/v5.json',
    VEGA_SCHEMA = os.path.join(ROOT_DIR, 'static/vega-v5.json'),
    VEGA_VERSION = '5',
    VEGA_DEFAULT_WIDTH = 400,
    VEGA_DEFAULT_HEIGHT = 400,
    VEGA_SITE_URL = 'https://vega.github.io/vega/',
    VEGA_EMBED_JS_URL = 'https://cdn.jsdelivr.net/npm/vega-embed@4',
    VEGA_LITE_SITE_URL = 'https://vega.github.io/vega-lite/',
    VEGA_LITE_JS_URL = 'https://cdn.jsdelivr.net/npm/vega-lite@3',
    VEGA_LITE_SCHEMA_URL = 'https://vega.github.io/schema/vega-lite/v3.json',
    VEGA_LITE_SCHEMA = os.path.join(ROOT_DIR, 'static/vega-lite-v3.json'),
    VEGA_LITE_VERSION = '3',
    VEGA_LITE_DEFAULT_WIDTH = 400,
    VEGA_LITE_DEFAULT_HEIGHT = 400,
)

app = flask.Flask(__name__, template_folder='html')
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['nameext'] = utils.NameExtConverter
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config.from_mapping(CONFIG)
app.config['SQLITE_VERSION'] = sqlite3.sqlite_version

# Modify the configuration from a JSON file.
try:
    filepath = os.environ['CONFIG_FILEPATH']
    app.config.from_json(filepath)
    # Raises an error if filepath variable defined, but no such file.
except KeyError:
    for filepath in [os.path.normpath(os.path.join(ROOT_DIR, 'config.json')),
                     os.path.normpath(os.path.join(ROOT_DIR, '../site/config.json'))]:
        try:
            app.config.from_json(filepath)
        except FileNotFoundError:
            filepath = None
        else:
            break
if filepath: print(' > Configuration file:', filepath)

# Sanity check configuration.
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
dbportal.system.init(app)

# Init the mail handler.
utils.mail.init_app(app)

# Set the URL map.
app.register_blueprint(dbportal.db.blueprint, url_prefix='/db')
app.register_blueprint(dbportal.dbs.blueprint, url_prefix='/dbs')
app.register_blueprint(dbportal.table.blueprint, url_prefix='/table')
app.register_blueprint(dbportal.query.blueprint, url_prefix='/query')
app.register_blueprint(dbportal.view.blueprint, url_prefix='/view')
app.register_blueprint(dbportal.index.blueprint, url_prefix='/index')
app.register_blueprint(dbportal.visual.blueprint, url_prefix='/visual')
app.register_blueprint(dbportal.template.blueprint, url_prefix='/template')
app.register_blueprint(dbportal.templates.blueprint, url_prefix='/templates')
app.register_blueprint(dbportal.vega.blueprint, url_prefix='/vega')
app.register_blueprint(dbportal.vega_lite.blueprint, url_prefix='/vega-lite')
app.register_blueprint(dbportal.user.blueprint, url_prefix='/user')
app.register_blueprint(dbportal.about.blueprint, url_prefix='/about')

app.register_blueprint(dbportal.api_db.blueprint, url_prefix='/api/db')
app.register_blueprint(dbportal.api_dbs.blueprint, url_prefix='/api/dbs')
app.register_blueprint(dbportal.api_table.blueprint, url_prefix='/api/table')
app.register_blueprint(dbportal.api_template.blueprint,
                       url_prefix='/api/template')
app.register_blueprint(dbportal.api_templates.blueprint,
                       url_prefix='/api/templates')
app.register_blueprint(dbportal.api_user.blueprint, url_prefix='/api/user')
app.register_blueprint(dbportal.api_schema.blueprint, url_prefix='/api/schema')

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils,
                enumerate=enumerate,
                len=len,
                range=range)

@app.template_filter('thousands')
def thousands(value):
    "Output integer with thousands delimiters."
    if isinstance(value, int):
        return '{:,}'.format(value)
    else:
        return value

@app.template_filter('none_as_literal_null')
def none_as_literal_null(value):
    "Output None as HTML '<NULL>' in safe mode."
    if value is None:
        return jinja2.utils.Markup('<i>&lt;NULL&gt;</i>')
    else:
        return value

@app.template_filter('none_as_empty_string')
def none_as_empty_string(value):
    "Output the value if not None, else an empty string."
    if value is None:
        return ''
    else:
        return value

@app.template_filter('access')
def access(value):
    "Output public or private according to the value."
    if value:
        return jinja2.utils.Markup('<span class="badge badge-info">public</span>')
    else:
        return jinja2.utils.Markup('<span class="badge badge-secondary">private</span>')

@app.template_filter('mode')
def mode(value):
    "Output readonly or read-write according to the value."
    if value:
        return jinja2.utils.Markup('<span class="badge badge-success">read-only</span>')
    else:
        return jinja2.utils.Markup('<span class="badge badge-warning">read/write</span>')

@app.before_request
def prepare():
    "Connect to the system database (read-only); get the current user."
    flask.g.cnx = dbportal.system.get_cnx()
    flask.g.current_user = dbportal.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == constants.ADMIN

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

@app.route('/')
def home():
    "Home page; display the list of public databases."
    return flask.render_template('home.html',
                                 dbs=dbportal.dbs.get_dbs(public=True))

@app.route('/api')
def api():
    "API home resource; links to other resources."
    data = {'title': 'DbPortal', 
             'version': CONFIG['VERSION'],
             'databases': {
                 'public': {'href': utils.url_for('api_dbs.public')}
             },
             'templates': {
                 'public': {'href': utils.url_for('api_templates.public')}
             },
             'display': {'href': utils.url_for('home'), 'format': 'html'}
    }
    if flask.g.current_user:
        data['databases']['owner'] = {
            'href': utils.url_for('api_dbs.owner',
                                  username=flask.g.current_user['username'])
        }
        data['templates']['owner'] = {
            'href': utils.url_for('api_templates.owner',
                                  username=flask.g.current_user['username'])
        }
    if flask.g.is_admin:
        data['databases']['all'] = {
            'href': utils.url_for('api_dbs.all')
        }
        data['templates']['all'] = {
            'href': utils.url_for('api_templates.all')
        }
    if flask.g.current_user:
        data['user'] = dbportal.api_user.get_api(flask.g.current_user['username'])
    result = utils.get_api(**data)
    result.pop('api') # Redundant
    return flask.jsonify(**result)


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
