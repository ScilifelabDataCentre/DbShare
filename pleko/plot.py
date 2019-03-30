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
import itertools
import json
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
        db = pleko.db.get_check_read(dbname, nrows=False)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template('plot/home.html', db=db)

@blueprint.route('/<name:dbname>/display/<name:plotname>',
                 methods=['GET', 'POST', 'DELETE'])
def display(dbname, plotname):
    "Display the plot."
    try:
        db = pleko.db.get_check_read(dbname)
        plot = get_plot(dbname, plotname)
        schema = pleko.db.get_schema(db, plot['tableviewname'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    return flask.render_template(
        'plot/display.html',
        db=db,
        schema=schema,
        plot=plot,
        has_write_access = pleko.db.has_write_access(db))

@blueprint.route('/<name:dbname>/create/<name:tableviewname>',
                 methods=['GET', 'POST'])
@pleko.user.login_required
def create(dbname, tableviewname):
    "Create a plot for the given table or view."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
        schema = pleko.db.get_schema(db, tableviewname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/create.html',
                                     db=db,
                                     schema=schema)
    elif utils.is_method_POST():
        try:
            with PlotContext(db, tableviewname=tableviewname) as ctx:
                ctx.set_plotname(flask.request.form.get('name'))
                ctx.set_spec(flask.request.form.get('spec'))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

@blueprint.route('/<name:dbname>/edit/<name:plotname>', 
                 methods=['GET', 'POST', 'DELETE'])
@pleko.user.login_required
def edit(dbname, plotname):
    "Edit the plot."
    try:
        db = pleko.db.get_check_write(dbname, plots=True)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))
    # Don't use 'get_plot'; info available in db dict.
    for plot in itertools.chain.from_iterable([i[1] for i in db['plots']]):
        if plot['name'] == plotname: break
    else:
        flask.flash('no such plot', 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))
    try:
        schema = pleko.db.get_schema(db, plot['tableviewname'])
    except ValueError:
        flask.flash('no such table or view', 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.is_method_GET():
        return flask.render_template('plot/edit.html', 
                                     db=db,
                                     plot=plot,
                                     schema=schema)
    elif utils.is_method_POST():
        try:
            with PlotContext(db, plot=plot) as ctx:
                ctx.set_spec(flask.request.form.get('spec'))
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            plotname=ctx.plot['name']))

    elif utils.is_method_DELETE():
        dbcnx = pleko.db.get_cnx(dbname, write=True)
        try:
            with dbcnx:
                sql = "DELETE FROM plot$ WHERE name=?"
                cursor = dbcnx.cursor()
                cursor.execute(sql, (plotname,))
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

def get_plots(dbname):
    """Get the plots for the database.
    List of tuples (tableviewname, plotlist), sorted by table/view and name.
    """
    cursor = pleko.db.get_cnx(dbname).cursor()
    sql = "SELECT name, tableviewname, spec FROM %s" % pleko.db.PLOT_TABLE_NAME
    cursor.execute(sql)
    plots = {}
    for row in cursor:
        plot = {'name': row[0],
                'tableviewname': row[1],
                'spec': json.loads(row[2])}
        plots.setdefault(plot['tableviewname'], []).append(plot)
    for plotlist in plots.values():
        plotlist.sort(key=lambda p: p['name'])
    return sorted(plots.items())
    
def get_plot(dbname, plotname):
    "Get a plot for the database."
    cursor = pleko.db.get_cnx(dbname).cursor()
    sql = "SELECT tableviewname, spec FROM %s WHERE name=?" \
          % pleko.db.PLOT_TABLE_NAME
    cursor.execute(sql, (plotname,))
    rows = list(cursor)
    if len(rows) != 1:
        raise ValueError('no such plot')
    row = rows[0]
    return {'name': plotname,
            'tableviewname': row[0],
            'spec': json.loads(row[1])}


class PlotContext:
    "Context handler to create, modify and save a plot definition."

    def __init__(self, db, plot=None, tableviewname=None):
        self.db = db
        if plot:
            self.plot = copy.deepcopy(plot)
            self.tableviewname = tableviewname or self.plot['tableviewname']
        else:
            self.plot = {}
            self.tableviewname = tableviewname

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        with self.dbcnx:
            if self.plot.get('tableviewname'): # Already exists; update
                sql = "UPDATE %s SET spec=? WHERE name=?" % \
                      pleko.db.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (json.dumps(self.plot['spec']),
                                         self.plot['name']))
            else:               # Insert into table
                sql = "INSERT INTO %s (name, tableviewname, spec)" \
                      " VALUES(?, ?, ?)" % pleko.db.PLOT_TABLE_NAME
                self.dbcnx.execute(sql, (self.plot['name'],
                                         self.tableviewname,
                                         json.dumps(self.plot['spec'])))

    @property
    def dbcnx(self):
        try:
            return self._dbcnx
        except AttributeError:
            # Don't close connection at exit; done externally to the context
            self._dbcnx = pleko.db.get_cnx(self.db['name'], write=True)
            return self._dbcnx

    def set_plotname(self, plotname):
        "Set the plot name."
        if not plotname:
            raise ValueError('no plot name given')
        if not constants.NAME_RX.match(plotname):
            raise ValueError('invalid plot name')
        if self.plot.get('name'):
            raise ValueError('cannot change the plot name')
        self.plot['name'] = plotname

    def set_tableviewname(self, tableviewname):
        if not tableviewname:
            raise ValueError('no table name given')
        if not constants.NAME_RX.match(tableviewname):
            raise ValueError('invalid table name')
        if self.plot.get('tableviewname'):
            raise ValueError('cannot change the tableviewname of the plot')
        self.plot['tableviewname'] = tableviewname

    def set_spec(self, spec):
        try:
            self.plot['spec'] = json.loads(spec)
            # XXX Check Vega-Lite JSON-Schema
        except (ValueError, TypeError) as error:
            raise ValueError(str(error))
