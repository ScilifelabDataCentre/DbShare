"Visualization endpoints."

import json

import flask
import http.client
import jsonschema
import sqlite3

import dbshare.db
import dbshare.user
from dbshare import constants
from dbshare import utils


blueprint = flask.Blueprint('visual', __name__)

@blueprint.route('/<name:dbname>/<nameext:visualname>')
def display(dbname, visualname): # NOTE: visualname is a NameExt instance!
    "Display the visualization."
    try:
        db = dbshare.db.get_check_read(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        visual = dbshare.db.get_visual(db, str(visualname))
        schema = dbshare.db.get_schema(db, visual['sourcename'])
        dbshare.db.set_nrows(db, targets=[schema['name']])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if visualname.ext in (None, 'html'):
        return flask.render_template(
            'visual/display.html',
            db=db,
            schema=schema,
            visual=visual,
            title="Visualization {}".format(visualname),
            has_write_access = dbshare.db.has_write_access(db))

    elif visualname.ext == 'json':
        return flask.jsonify(utils.get_api(**visual['spec']))

    else:
        flask.abort(http.client.NOT_ACCEPTABLE)

@blueprint.route('/<name:dbname>/<name:visualname>/edit', 
                 methods=['GET', 'POST', 'DELETE'])
@dbshare.user.login_required
def edit(dbname, visualname):
    "Edit the visualization. Or delete it."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        visual = dbshare.db.get_visual(db, visualname)
        schema = dbshare.db.get_schema(db, visual['sourcename'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

    if utils.http_GET():
        dbshare.db.set_nrows(db, targets=[schema['name']])
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
                    dbshare.db.get_visual(db, newname)
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
            with dbshare.db.DbContext(db) as ctx:
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

    elif utils.http_DELETE():
        try:
            with dbshare.db.DbContext(db) as ctx:
                ctx.delete_visual(str(visualname))
        except sqlite3.Error as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

@blueprint.route('/<name:dbname>/<name:visualname>/clone',
                 methods=['GET','POST'])
@dbshare.user.login_required
def clone(dbname, visualname):
    "Clone the visualization."
    try:
        db = dbshare.db.get_check_write(dbname)
    except (KeyError, ValueError) as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('home'))
    try:
        visual = dbshare.db.get_visual(db, visualname)
        schema = dbshare.db.get_schema(db, visual['sourcename'])
    except ValueError as error:
        flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('db.display', dbname=dbname))

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
                dbshare.db.get_visual(db, visualname)
            except ValueError:
                pass
            else:
                raise ValueError('visual name already in use')
            with dbshare.db.DbContext(db) as ctx:
                ctx.add_visual(visualname, schema['name'], visual['spec'])
        except (ValueError, sqlite3.Error) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('db.display', dbname=dbname))
        return flask.redirect(flask.url_for('.display',
                                            dbname=dbname,
                                            visualname=visualname))
