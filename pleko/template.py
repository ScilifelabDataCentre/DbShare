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
    return flask.render_template('template/create.html')

@blueprint.route('/<name:templatename>')
@pleko.user.login_required
def view(templatename):
    "View the template definition."
    raise NotImplementedError

@blueprint.route('/<name:templatename>/edit')
@pleko.user.login_required
def edit(templatename):
    "Edit the template definition."
    raise NotImplementedError

@blueprint.route('/<name:templatename>/field')
@pleko.user.login_required
def field(templatename):
    "Add an input field to the template definition."
    raise NotImplementedError

@blueprint.route('/<name:templatename>/render/<name:dbname>/<name:sourcename>')
@pleko.user.login_required
def render(templatename):
    "Render the given source (table or view) with the given template."
    raise NotImplementedError

def get_templates(public=None, owner=None):
    "Get a list of templates according to criteria."
    sql = "SELECT name FROM templates"
    criteria = {}
    if public is not None:
        criteria['public=?'] = public
    if owner:
        criteria['owner=?'] = owner
    if criteria:
        sql += ' WHERE ' + ' AND '.join(criteria.keys())
    cursor = pleko.master.get_cursor()
    cursor.execute(sql, tuple(criteria.values()))
    return [get_template(row[0]) for row in cursor]

def get_template(name,):
    """Return the database metadata for the given name.
    Return None if no such database.
    """
    cursor = pleko.master.get_cursor()
    sql = "SELECT owner, title, description, code, public," \
          " created, modified FROM templates WHERE name=?"
    cursor.execute(sql, (name,))
    rows = list(cursor)
    if len(rows) != 1: return None # 'rowcount' does not work?!
    row = rows[0]
    template = {'name':       name,
                'owner':      row[0],
                'title':      row[1],
                'description':row[2],
                'code':       row[3],
                'public':     bool(row[4]),
                'created':    row[5],
                'modified':   row[6]}
    return template
