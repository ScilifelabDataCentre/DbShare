"The Pleko web app."

import importlib
import logging

import flask

import pleko
from pleko import constants
from pleko import utils

app = flask.Flask(__name__)
app.config.from_object(pleko.DefaultConfig)
app.config.from_json('config.json')

app.url_map.converters['iuid'] = utils.IuidConverter
app.url_map.converters['id'] = utils.IdentifierConverter
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.session.permanent = True

user_dbi = importlib.import_module(app.config.USER_DBI['MODULE'])

if not app.config.SECRET_KEY:
    raise ValueError('SECRET_KEY not defined')
if not app.config.HASH_SALT:
    raise ValueError('HASH_SALT not defined')
if app.config.LOGGING_DEBUG:
    kwargs = dict(level=logging.DEBUG)
else:
    kwargs = dict(level=logging.INFO)
logging.basicConfig(**kwargs)
logging.info("Pleko version %s", pleko.__version__)
logging.debug('logging debug')


@app.before_first_request
def init_userdbi():
    "Initialize the user database, if not done."
    user_dbi.UserDb().initialize()

@app.before_request
def set_userdb():
    "Set the user database interface object."
    flask.g.userdb = user_dbi.UserDb()

@app.before_request
def get_user():
    "Get the logged-in user from the session cookie."
    try:
        try:
            flask.g.user = flask.g.userdb[flask.session['username']]
        except KeyError:
            pass                # XXX Try API key
        else:
            if flask.session['expires'] <= utils.get_time():
                do_logout()
                raise KeyError
            flask.g.is_admin = flask.g.user.get('role') == constants.ADMIN
    except KeyError:
        flask.g.user = None
        flask.g.is_admin = False

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                utils=utils)

@app.route('/')
def home():
    "Home page."
    return flask.render_template('home.html')

@aoo.route('/register')
def register():
    "Register a new user account."
    if utils.is_method_GET():
        return flask.render_template('register.html')
    elif utils.is_method_POST():
        # XXX depending on direct enable or not
        return flask.redirect(flask.url_for('home'))

@app.route('/login', methods=["GET", "POST"])
def login():
    "Login to a user account."
    if utils.is_method_GET():
        return flask.render_template('login.html')
    if utils.is_method_POST():
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        try:
            if username and password:
                user = flask.g.db.get_user(username)
                utils.check_password(user, password)
                flask.session['username'] = user['username']
                flask.session['expires'] = utils.get_time(settings.MAX_SESSION_AGE)
            else:
                raise ValueError('username and/or password missing')
            try:
                return flask.redirect(flask.request.form['next'])
            except KeyError:
                return flask.redirect(flask.url_for('home'))
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('login'))

def get_hashed(s):
    h = hashlib.sha256()
    h.update(settings.HASH_SALT.encode('utf-8'))
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def check_password(user, password):
    if not user or user.get('password') != get_hashed(password):
        raise ValueError('wrong username and/or password')


# This code is used only during testing.
if __name__ == '__main__':
    app.run()
