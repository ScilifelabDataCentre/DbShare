"The Pleko web app."

import sqlite3

import flask

import pleko
import pleko.constants
import pleko.utils
import pleko.user
import pleko.resource

def create_app():
    "Return the configured app object. Initialize the masterdb, if not done."
    app = flask.Flask(__name__)
    app.config.from_mapping(pleko.default_config)
    app.config.from_json('config.json')
    app.url_map.converters['iuid'] = pleko.utils.IuidConverter
    app.url_map.converters['id'] = pleko.utils.IdentifierConverter
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    db = pleko.utils.get_masterdb(app)
    pleko.user.init_masterdb(db)
    pleko.resource.init_masterdb(db)
    pleko.utils.mail.init_app(app)
    return app

app = create_app()
app.register_blueprint(pleko.user.blueprint, url_prefix='/user')
app.register_blueprint(pleko.resource.blueprint, url_prefix='/resource')


@app.before_request
def prepare():
    "Connect to the master database; get the current user."
    flask.g.db = pleko.utils.get_masterdb()
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
    resources = pleko.resource.get_resources(public=not flask.g.is_admin)
    return flask.render_template('index.html', resources=resources)


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)
