"The Pleko web app."

import flask

import pleko
from pleko import constants
from pleko import utils
from pleko import user

def create_app():
    "Return the configured app object."
    app = flask.Flask(__name__)
    app.config.from_mapping(pleko.default_config)
    app.config.from_json('config.json')
    app.url_map.converters['iuid'] = utils.IuidConverter
    app.url_map.converters['id'] = utils.IdentifierConverter
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    user.init_app(app)
    app.register_blueprint(user.blueprint)
    utils.mail.init_app(app)
    return app

app = create_app()

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
