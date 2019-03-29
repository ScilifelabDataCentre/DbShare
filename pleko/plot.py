"""Pleko plot endpoints.

/plot/<dbname>
  List of plots.

/plot/<dbname>/display/<plotname>
  Display.

/plot/<dbname>/create/<tableviewname>
  Create plot for the given table or view.

/plot/<dbname>/edit/<plotname>
  Edit.
"""

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

@blueprint.route('/<name:dbname>')
def home(dbname):
    "List the plots in the database."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('plot/home.html',
                                 db=db,
                                 plots=utils.sorted_schema(get_plots(dbname)))

@blueprint.route('/<name:dbname>')
def display(dbname, tvname):
    "Display the plot."
    try:
        db = pleko.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

def get_plots(dbname):
    "Get the plots in the database."
    try:
        with open(utils.plotpath(dbname)) as infile:
            return json.load(infile)
    except FileNotFoundError:
        return {}


class PlotContext:
    "Context handler to create, modify and save a plot definition."

    def __init__(self, dbname, plotname):
        self.dbname = dbname
        self.plots = get_plots(self.dbname)
        self.plot = copy.deepcopy(self.plots.get(self.plotname) or {})
        self.set_plotname(plotname)

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        self.plots[self.plot['name']] = self.plot
        with open(self.filepath, 'w') as outfile:
            json.dump(self.plots, outfile, indent=2)

    def set_plotname(self, plotname):
        if not plotname:
            raise ValueError('no plot name given')
        if not constants.NAME_RX.match(plotname):
            raise ValueError('invalid plot name')
        if plotname in self.plots:
            raise ValueError('plot name already exists')
        self.plot['name'] = plotname
