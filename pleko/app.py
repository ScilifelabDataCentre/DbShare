"The Pleko web app."

import importlib
import logging

import flask

import pleko
from pleko import constants
from pleko import settings
from pleko import utils

settings.load()
user_dbi = importlib.import_module(settings.USER_DBI['MODULE'])

app = flask.Flask(__name__)

app.secret_key = settings.SECRET_KEY
if settings.PREFERRED_URL_SCHEME:
    app.config['PREFERRED_URL_SCHEME'] = settings.PREFERRED_URL_SCHEME
if settings.SERVER_NAME:
    app.config['SERVER_NAME'] = settings.SERVER_NAME
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.url_map.converters['iuid'] = utils.IuidConverter
app.url_map.converters['id'] = utils.IdentifierConverter
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.before_first_request
def init_userdbi():
    user_dbi.UserDb().initialize()

@app.before_request
def set_userdb():
    "Set the user database interface object."
    flask.g.userdb = user_dbi.UserDb()

@app.before_request
def get_login_user():
    "Get the logged-in user according to the session cookie."
    # try:
    #     try:
    #         flask.g.user = flask.g.db.get_user(flask.session['username'])
    #     except KeyError:
    #         auth = flask.request.headers['Authorization']
    #         if not auth.startswith('Basic'): raise KeyError
    #         auth = base64.b64decode(auth[6:])
    #         try:
    #             username, password = auth.decode('utf-8').split(':', 1)
    #             user = flask.g.db.get_user(username)
    #             utils.check_password(user, password)
    #             flask.g.user = user
    #         except (IndexError, ValueError):
    #             raise KeyError
    #     else:
    #         if flask.g.user:
    #             if flask.session['expires'] <= utils.get_time():
    #                 do_logout()
    #                 raise KeyError
    # except KeyError:
    #     flask.g.user = None
    # flask.g.is_admin = flask.g.user and flask.g.user['role'] == constants.ADMIN

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                settings=settings,
                utils=utils)

@app.route('/')
def home():
    return flask.render_template('base.html')

@app.route('/user/<name>')
def user(name):
    return "<h1>Hello {}!</h1>".format(name)


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=settings.FLASK_DEBUG)
