"The Pleko web app."

import flask

import pleko
from pleko import constants
from pleko import utils
from pleko import user

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

user.initialize(app.config)
app.register_blueprint(user.blueprint)

app.logger.info("Pleko version %s", pleko.__version__)


@app.before_request
def user_setup():
    user.setup(app.config)

@app.before_request
def get_current_user():
    flask.g.current_user = user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == constants.ADMIN


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


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
