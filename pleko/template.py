"Visualization template endpoints."

import flask
import jsonschema
import sqlite3

import pleko.db
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('template', __name__)

@blueprint.route('/')
@pleko.user.login_required
def create():
    "Create a template."
    raise NotImplementedError

@blueprint.route('/<name:templatename>')
@pleko.user.login_required
def view(templatename):
    "Select source (table or view) to render by the template."
    raise NotImplementedError
