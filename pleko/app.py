"The Pleko web app."

import sqlite3

import flask

import pleko
import pleko.constants
import pleko.utils
import pleko.user

def create_app():
    "Return the configured app object."
    app = flask.Flask(__name__)
    app.config.from_mapping(pleko.default_config)
    app.config.from_json('config.json')
    app.url_map.converters['iuid'] = pleko.utils.IuidConverter
    app.url_map.converters['id'] = pleko.utils.IdentifierConverter
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    pleko.user.init_app(app)
    app.register_blueprint(pleko.user.blueprint, url_prefix='/user')
    pleko.utils.mail.init_app(app)
    return app

app = create_app()

@app.before_request
def connect_masterdb():
    flask.g.db = sqlite3.connect(flask.current_app.config['MASTERDB_FILEPATH'])
    flask.g.db.execute('PRAGMA foreign_keys = ON')

@app.before_request
def get_current_user():
    flask.g.current_user = pleko.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user.get('role') == pleko.constants.ADMIN


@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context for templates."
    return dict(constants=pleko.constants,
                csrf_token=pleko.utils.csrf_token,
                utils=pleko.utils)

@app.route('/')
def index():
    "Home page."
    return flask.render_template('index.html')


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
