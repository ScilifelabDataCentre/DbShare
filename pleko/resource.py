"Resource; abstract data container."

import json

import flask

from pleko import utils
from pleko.user import login_required
import pleko.reldb


def init_masterdb(db):
    "Initialize resource tables in the master database, if not done."
    db.execute("CREATE TABLE IF NOT EXISTS resources"
               "(rid TEXT PRIMARY KEY,"
               " type TEXT NOT NULL,"
               " owner TEXT NOT NULL REFERENCES users (username),"
               " description TEXT,"
               " public INTEGER NOT NULL,"
               " profile TEXT NOT NULL,"
               " created TEXT NOT NULL,"
               " modified TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS resources_logs"
               "(rid TEXT NOT NULL REFERENCES resources (rid),"
               " new TEXT NOT NULL,"
               " editor TEXT,"
               " remote_addr TEXT,"
               " user_agent TEXT,"
               " timestamp TEXT NOT NULL)")
    db.execute("CREATE INDEX IF NOT EXISTS resources_logs_rid_ix"
               " ON resources_logs (rid)")

def get_resource(rid, db=None):
    """Return the resource for the given identifier.
    Return None if no such resource.
    Does *not* check access.
    """
    if db is None:
        db = flask.g.db
    sql = "SELECT type, owner, description, public, profile," \
          " created, modified FROM resources WHERE rid=?"
    cursor = db.cursor()
    cursor.execute(sql, (rid,))
    rows = list(cursor)
    if len(rows) != 1: return None
    row = rows[0]
    return {'rid':         rid,
            'type':        row[0],
            'owner':       row[1],
            'description': row[2],
            'public':      bool(row[3]),
            'profile':     json.loads(row[4]),
            'created':     row[5],
            'modified':    row[6]}



blueprint = flask.Blueprint('resource', __name__)

@blueprint.route('/', methods=["GET", "POST"])
@login_required
def create():
    if utils.is_method_GET():
        return flask.render_template('create.html')
    if utils.is_method_POST():
        try:
            with ResourceContext() as ctx:
                rid = flask.request.form['rid']
                ctx.set_rid(rid)
                type = flask.request.form['type']
                ctx.set_type(type)
                ctx.set_description(flask.request.form.get('description'))
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/<id:rid>/logs')
def logs(rid):
    resource = get_resource(rid=rid)
    if resource is None:
        flask.flash('no such resource', 'error')
        return flask.redirect(flask.url_for('index'))
    if not has_read_access(resource):
        flask.flash('access not allowed', 'error')
        return flask.redirect(flask.url_for('index'))
    cursor = flask.g.db.cursor()
    sql = "SELECT new, editor, remote_addr, user_agent, timestamp" \
          " FROM resources_logs WHERE rid=? ORDER BY timestamp DESC"
    cursor.execute(sql, (resource['rid'],))
    logs = [{'new': json.loads(row[0]),
             'editor': row[1],
             'remote_addr': row[2],
             'user_agent': row[3],
             'timestamp': row[4]}
            for row in cursor]
    return flask.render_template('resource_logs.html',
                                 resource=resource,
                                 logs=logs)

class ResourceContext:
    "Context for creating, modifying and saving a resource."

    def __init__(self, resource=None):
        if resource is None:
            self.resource = {'owner': flask.g.current_user['username'],
                             'profile': {},
                             'created': utils.get_time()}
            self.orig = {}
        else:
            self.resource = resource
            self.orig = resource.copy()
        self.db = utils.get_masterdb()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['rid', 'type', 'owner']:
            if not self.resource.get(key):
                raise ValueError("invalid resource: %s not set" % key)
        self.resource['modified'] = utils.get_time()
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM resources WHERE rid=?",
                       (self.resource['rid'],))
        rows = list(cursor)
        with self.db:
            # Update resource
            if rows[0][0]:
                sql = "UPDATE resources SET owner=?, description=?," \
                      " public=?, profile=?, modified=?" \
                      " WHERE resourcename=?"
                self.db.execute(sql, (self.resource['owner'],
                                      self.resource.get('description'),
                                      bool(self.resource.get('public')),
                                      json.dumps(self.resource['profile'],
                                                 ensure_ascii=False),
                                      self.resource['modified'],
                                      self.resource['rid']))
            # Create resource
            else:
                if type == pleko.constants.RELDB:
                    pleko.reldb.create(self.resource['rid'])
                sql = "INSERT INTO resources" \
                      " (rid, type, owner, description, public," \
                      "  profile, created, modified)" \
                      " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                self.db.execute(sql, (self.resource['rid'],
                                      self.resource['type'],
                                      self.resource['owner'],
                                      self.resource.get('description'),
                                      bool(self.resource.get('public')),
                                      json.dumps(self.resource['profile'],
                                                 ensure_ascii=False),
                                      self.resource['created'], 
                                      self.resource['modified']))
            # Add log entry
            new = {}
            for key, value in self.resource.items():
                if value != self.orig.get(key):
                    new[key] = value
            new.pop('modified')
            try:
                editor = flask.g.current_user['username']
            except AttributeError:
                editor = None
            if flask.has_request_context():
                remote_addr = str(flask.request.remote_addr)
                user_agent = str(flask.request.user_agent)
            else:
                remote_addr = None
                user_agent = None
            sql = "INSERT INTO resources_logs (rid, new, editor," \
                  " remote_addr, user_agent, timestamp)" \
                  " VALUES (?, ?, ?, ?, ?, ?)"
            self.db.execute(sql, (self.resource['rid'],
                                  json.dumps(new, ensure_ascii=False),
                                  editor,
                                  remote_addr,
                                  user_agent,
                                  utils.get_time()))

    def set_rid(self, rid):
        if 'rid' in self.resource:
            raise ValueError('resource identifier cannot be changed')
        if not pleko.constants.IDENTIFIER_RX.match(rid):
            raise ValueError('invalid resource identifier')
        if get_resource(rid=rid, db=self.db):
            raise ValueError('resource identifier already in use')
        self.resource['rid'] = rid

    def set_type(self, type):
        if 'type' in self.resource:
            raise ValueError('resource type cannot be changed')
        if type not in pleko.constants.RESOURCE_TYPES:
            raise ValueError('invalid resource type')
        self.resource['type'] = type

    def set_description(self, description):
        self.resource['description'] = description or None
