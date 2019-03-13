"Resource; abstract data container."

import flask

import pleko.utils
from pleko.user import (get_current_user,
                        login_required,
                        admin_required)


def init_masterdb(db):
    "Initialize resource tables in the master database, if not done."
    db.execute("CREATE TABLE IF NOT EXISTS resources"
               "(rid PRIMARY KEY,"
               " type TEXT NOT NULL,"
               " owner TEXT NOT NULL REFERENCES users (username),"
               " description TEXT,"
               " public INTEGER NOT NULL,"
               " profile TEXT NOT NULL,"
               " created TEXT NOT NULL,"
               " modified TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS resources_logs"
               "(rid TEXT NOT NULL REFERENCES resources (rid),"
               " action TEXT NOT NULL,"
               " editor TEXT,"
               " remote_addr TEXT,"
               " user_agent TEXT,"
               " timestamp TEXT NOT NULL)")
    db.execute("CREATE INDEX IF NOT EXISTS resources_logs_rid_ix"
               " ON resources_logs (rid)")

def get_resources(public=True, db=None):
    "Get a list of all resources."
    if db is None:
        db = pleko.utils.get_masterdb()
    sql = "SELECT rid, type, owner, description, public, profile," \
          " created, modified FROM resources"
    if public:
        sql += " WHERE public=1"
    cursor = db.cursor()
    cursor.execute(sql)
    return [{'rid':         row[0],
             'type':        row[1],
             'owner':       row[2],
             'description': row[3],
             'public':      row[4],
             'profile':     json.loads(row[5]),
             'created':     row[6],
             'modified':    row[7]}
            for row in cursor]


blueprint = flask.Blueprint('resource', __name__)

@blueprint.route('/', methods=["GET", "POST"])
@login_required
def index():
    if pleko.utils.is_method_GET():
        return flask.render_template('resource/index.html')
    if pleko.utils.is_method_POST():
        try:
            with ResourceContext() as ctx:
                ctx.set_rid(flask.request.form['rid'])
                ctx.set_type(flask.request.form['type'])
        except (KeyError, ValueError) as error:
            flask.flash(str(error), 'error')
            return flask.redirect(flask.url_for('index'))


class ResourceContext:
    "Context for creating, modifying and saving a resource."

    def __init__(self, resource=None):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        raise NotImplementedError

    def set_rid(self, rid):
        raise NotImplementedError

    def set_type(self, type):
        raise NotImplementedError
