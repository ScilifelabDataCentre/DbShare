"Pleko plot endpoints."

import copy
import json
import os
import os.path
import sqlite3

import flask

import pleko.db
import pleko.master
import pleko.user
from pleko import constants
from pleko import utils


blueprint = flask.Blueprint('plot', __name__)

@blueprint.route('/<name:dbname>/<name:tvname>', methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, tvname):
    "Create a plot of a table or view in the database."
    try:
        db = pleko.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    try:
        schema = get_schema(db, tvname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home',
                                            dbname=dbname,
                                            schema=schema))

    if utils.is_method_GET():
        return flask.render_template('plot/create.html', db=db, schema=schema)

    elif utils.is_method_POST():
        try:
            plot = json.loads(flask.request.form.get('json'))
        except (ValueError, TypeError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        with PlotContext(dbname, flask.request.form.get('name')) as ctx:
            ctx.plot = plot
        return flask.redirect(flask.url_for('db.home', dbname=dbname))


def get_schema(db, tvname):
    "Get table or view schema from the database. Raise KeyError if none."
    try:
        schema = db['tables'][tvname]
        schema['type'] = 'table'
    except KeyError:
        try:
            schema = db['views'][tvname]
            schema['type'] = 'view'
        except KeyError:
            raise ValueError('no such table or view')
    return schema


class PlotContext:
    "Context handler to create, modify and save a plot definition."

    def __init__(self, dbname, plotname):
        self.filepath = utils.dbpath('_plots_' + dbname, ext='.json')
        try:
            with open(self.filepath) as infile:
                self.plots = json.load(infile)
        except FileNotFoundError:
            self.plots = {}
        self.set_plotname(plotname)
        self.plot = copy.deepcopy(self.plots.get(self.plotname) or {})

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        self.plots[self.plotname] = self.plot
        with open(self.filepath, 'w') as outfile:
            json.dump(self.plots, outfile, indent=2)

    def set_plotname(self, plotname):
        if not plotname:
            raise ValueError('no plot name given')
        if not constants.NAME_RX.match(plotname):
            raise ValueError('invalid plot name')
        self.plotname = plotname
