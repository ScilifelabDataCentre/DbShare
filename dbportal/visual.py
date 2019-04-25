"Visualization endpoints."

import json

import flask
import jsonschema
import sqlite3

import dbportal.db
import dbportal.user
from dbportal import constants
from dbportal import utils


blueprint = flask.Blueprint('visual', __name__)

@blueprint.route('/<name:dbname>')
def home(dbname):
    "List the visualizations in the database."
    try:
        db = dbportal.db.get_check_read(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    write_access = dbportal.db.has_write_access(db)
    return flask.render_template('visual/home.html',
                                 db=db,
                                 has_write_access=write_access)

@blueprint.route('/<name:dbname>/<nameext:visualname>',
                 methods=['GET', 'POST', 'DELETE'])
def display(dbname, visualname): # NOTE: visualname is a NameExt instance!
    "Display the visualization. Or delete it."
    if utils.http_GET():
        try:
            db = dbportal.db.get_check_read(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        try:
            visual = dbportal.db.get_visual(db, str(visualname))
            schema = dbportal.db.get_schema(db, visual['sourcename'])
            dbportal.db.set_nrows(db, nrows=[schema['name']])
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))

        if visualname.ext is None or visualname.ext == 'html':
            return flask.render_template(
                'visual/display.html',
                db=db,
                schema=schema,
                visual=visual,
                title="Visualization {}".format(visualname),
                has_write_access = dbportal.db.has_write_access(db))
        elif visualname.ext == 'json':
            data = {'$id': flask.request.url}
            data.update(visual['spec'])
            return flask.jsonify(data)
        else:
            flask.abort(406)

    elif utils.http_DELETE():
        try:
            db = dbportal.db.get_check_write(dbname)
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('home'))
        try:
            visual = dbportal.db.get_visual(db, str(visualname))
            schema = dbportal.db.get_schema(db, visual['sourcename'])
        except ValueError as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))

        try:
            with dbportal.db.DbContext(db) as ctx:
                ctx.delete_visual(str(visualname))
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('.home', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:visualname>/edit', 
                 methods=['GET', 'POST'])
@dbportal.user.login_required
def edit(dbname, visualname):
    "Edit the visualization."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        visual = dbportal.db.get_visual(db, visualname)
        schema = dbportal.db.get_schema(db, visual['sourcename'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        dbportal.db.set_nrows(db, nrows=[schema['name']])
        return flask.render_template('visual/edit.html',
                                     db=db,
                                     schema=schema,
                                     visual=visual)
    elif utils.http_POST():
        try:
            newname = flask.request.form.get('name') or visualname
            strspec = flask.request.form.get('spec')
            if not newname:
                raise ValueError('no visual name given')
            if not constants.NAME_RX.match(newname):
                raise ValueError('invalid visual name')
            newname = newname.lower()
            if newname != visualname:
                try:
                    dbportal.db.get_visual(db, newname)
                except ValueError:
                    pass
                else:
                    raise ValueError('visual name already in use')
            if not strspec:
                raise ValueError('no spec given')
            spec = json.loads(strspec)
            jsonschema.validate(
                instance=spec,
                schema=flask.current_app.config['VEGA_LITE_SCHEMA'])
            with dbportal.db.DbContext(db) as ctx:
                ctx.update_visual(visualname, spec, newname)
        except (ValueError, TypeError,
                sqlite3.Error, jsonschema.ValidationError) as error:
            flask.flash(str(error), 'error')
            return flask.render_template('visual/edit.html', 
                                         db=db,
                                         visual=visual,
                                         spec=strspec, # Spec maybe with errors
                                         schema=schema)
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            visualname=newname))

@blueprint.route('/<name:dbname>/<name:visualname>/clone',
                 methods=['GET','POST'])
@dbportal.user.login_required
def clone(dbname, visualname):
    "Clone the visualization."
    try:
        db = dbportal.db.get_check_write(dbname)
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        visual = dbportal.db.get_visual(db, visualname)
        schema = dbportal.db.get_schema(db, visual['sourcename'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.home', dbname=dbname))

    if utils.http_GET():
        return flask.render_template('visual/clone.html', db=db, visual=visual)

    elif utils.http_POST():
        try:
            visualname = flask.request.form.get('name')
            if not visualname:
                raise ValueError('no visual name given')
            if not constants.NAME_RX.match(visualname):
                raise ValueError('invalid visual name')
            visualname = visualname.lower()
            try:
                dbportal.db.get_visual(db, visualname)
            except ValueError:
                pass
            else:
                raise ValueError('visual name already in use')
            with dbportal.db.DbContext(db) as ctx:
                ctx.add_visual(visualname, schema['name'], visual['spec'])
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.home', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            visualname=visualname))
