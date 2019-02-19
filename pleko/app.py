"The Pleko web app."

import importlib

import flask

import pleko
from pleko import constants
from pleko import utils
from pleko.auth import auth_blueprint

DEFAULT_CONFIG = dict(
    VERSION = pleko.__version__,
    SITE_NAME = 'Pleko',
    GITHUB_URL = 'https://github.com/pekrau/Pleko',
    SECRET_KEY = None,
    SALT_LENGTH = 12,
    REGISTRATION_DIRECT = False,
    REGISTRATION_WHITELIST = [],
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    USER_DBI_MODULE = None,
    CONTACT_EMAIL = None,
    EMAIL_HOST = None
)

app = flask.Flask(__name__)
app.config.from_mapping(DEFAULT_CONFIG)
app.config.from_json('config.json')

app.url_map.converters['iuid'] = utils.IuidConverter
app.url_map.converters['id'] = utils.IdentifierConverter
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.register_blueprint(auth_blueprint)

userdb = importlib.import_module(app.config['USERDB_MODULE'])

app.logger.info("Pleko version %s", pleko.__version__)


@app.before_first_request
def init_userdb():
    "Initialize the user database, if not done."
    userdb.UserDb(app.config).initialize()

@app.before_request
def setup_userdb():
    "Set the user database interface object."
    flask.g.userdb = userdb.UserDb(app.config)

@app.before_request
def get_session_user():
    "Get the logged-in user from the session cookie."
    flask.g.user = None
    try:
        try:
            flask.g.user = flask.g.userdb[flask.session['username']]
        except KeyError:
            pass                # XXX Try API key
        else:
            if flask.session['expires'] <= utils.get_time():
                flask.session.pop('username', None)
                raise KeyError
    except KeyError:
        pass
    flask.g.is_admin = flask.g.user and \
                       flask.g.user.get('role') == constants.ADMIN

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils)

@app.route('/')
def index():
    "Home page."
    return flask.render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    "Register a new user account."
    if utils.is_method_GET():
        return flask.render_template('register.html')
    elif utils.is_method_POST():
        try:
            user = flask.g.userdb.create(flask.request.form.get('username'),
                                         flask.request.form.get('email'),
                                         flask.request.form.get('password'),
                                         status=constants.ENABLED)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('register'))
        flask.flash('user account created')
        return flask.redirect(flask.url_for('user', identifier=user['username']))

@app.route('/user/<id:identifier>')
@utils.login_required
def user(identifier):
    try:
        user = flask.g.userdb[identifier]
    except KeyError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))
    if not (flask.g.is_admin or
            (flask.g.user and flask.g.user['username'] == user['username'])):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('user.html', user=user)


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
