"User display and login/logout HTMl endpoints."

import http.client
import json
import re
import sqlite3

import flask
import werkzeug.security

import dbshare.system

from . import constants
from . import utils


blueprint = flask.Blueprint("user", __name__)


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    "Login to a user account."
    if utils.http_GET():
        return flask.render_template(
            "user/login.html", next=flask.request.args.get("next")
        )
    if utils.http_POST():
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        try:
            if username and password:
                do_login(username, password)
            else:
                raise ValueError
            try:
                next = flask.request.form["next"]
            except KeyError:
                return flask.redirect(flask.url_for("dbs.owner", username=username))
            else:
                return flask.redirect(next)
        except ValueError:
            utils.flash_error("invalid user/password, or account disabled")
            return flask.redirect(flask.url_for(".login"))


def do_login(username, password):
    """Set the session cookie if successful login.
    Raise ValueError if some problem.
    """
    user = get_user(username)
    if user is None:
        raise ValueError
    if not werkzeug.security.check_password_hash(user["password"], password):
        raise ValueError
    if user["status"] != constants.ENABLED:
        raise ValueError
    flask.session["username"] = user["username"]
    flask.session.permanent = True


@blueprint.route("/logout", methods=["POST"])
def logout():
    "Logout from the user account."
    flask.session.pop("username", None)
    return flask.redirect(flask.url_for("home"))


@blueprint.route("/create", methods=["GET", "POST"])
@utils.admin_required
def create():
    "Create a new user account."
    if utils.http_GET():
        return flask.render_template("user/create.html")

    elif utils.http_POST():
        try:
            with UserSaver() as ctx:
                ctx.set_username(flask.request.form.get("username"))
                ctx.set_email(flask.request.form.get("email"))
                ctx.set_role(constants.USER)
                ctx.set_password(flask.request.form.get("password"))
            user = ctx.user
        except ValueError as error:
            utils.flash_error(error)
            return flask.redirect(flask.url_for(".create"))
        return flask.redirect(flask.url_for(".display", username=user["username"]))


@blueprint.route("/display")
@blueprint.route("/display/<name:username>")
@utils.login_required
def display(username=None):
    "Display the given user."
    if not username:
        username = flask.g.current_user["username"]
    user = get_user(username=username)
    if user is None:
        utils.flash_error("no such user")
        return flask.redirect(flask.url_for("home"))
    if not is_admin_or_self(user):
        utils.flash_error("access not allowed")
        return flask.redirect(flask.url_for("home"))
    ndbs, total_size = dbshare.db.get_usage(username)
    deletable = ndbs == 0
    return flask.render_template(
        "user/display.html",
        user=user,
        enable_disable=is_admin_and_not_self(user),
        ndbs=ndbs,
        total_size=total_size,
        deletable=deletable,
    )


@blueprint.route("/display/<name:username>/edit", methods=["GET", "POST", "DELETE"])
@utils.admin_required
def edit(username):
    "Edit the user. Or delete the user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("no such user")
        return flask.redirect(flask.url_for("home"))

    if utils.http_GET():
        return flask.render_template(
            "user/edit.html", user=user, change_role=is_admin_and_not_self(user)
        )

    elif utils.http_POST():
        with UserSaver(user) as ctx:
            email = flask.request.form.get("email")
            if email != user["email"]:
                ctx.set_email(enail)
            if flask.request.form.get("apikey"):
                ctx.set_apikey()
            if is_admin_and_not_self(user):
                ctx.set_role(flask.request.form.get("role"))
            quota = flask.request.form.get("quota") or None
            if quota:
                try:
                    quota = int(quota)
                except (ValueError, TypeError):
                    quota = -1
            ctx.set_quota(quota)
            password = flask.request.form.get("password")
            if password:
                ctx.set_password(password)
        return flask.redirect(flask.url_for(".display", username=user["username"]))

    elif utils.http_DELETE():
        ndbs, total_size = dbshare.db.get_usage(username)
        if ndbs != 0:
            utils.flash_error("cannot delete non-empty user account")
            return flask.redirect(flask.url_for(".display", username=username))
        cnx = utils.get_cnx(write=True)
        with cnx:
            sql = "DELETE FROM users_logs WHERE username=?"
            cnx.execute(sql, (username,))
            sql = "DELETE FROM users WHERE username=?"
            cnx.execute(sql, (username,))
        utils.flash_message(f"Deleted user {username}.")
        return flask.redirect(flask.url_for(".users"))


@blueprint.route("/display/<name:username>/logs")
@utils.login_required
def logs(username):
    "Display the log records of the given user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("no such user")
        return flask.redirect(flask.url_for("home"))
    if not is_admin_or_self(user):
        utils.flash_error("access not allowed")
        return flask.redirect(flask.url_for("home"))
    sql = (
        "SELECT new, editor, remote_addr, user_agent, timestamp"
        " FROM users_logs WHERE username=? ORDER BY timestamp DESC"
    )
    logs = [
        {
            "new": json.loads(row[0]),
            "editor": row[1],
            "remote_addr": row[2],
            "user_agent": row[3],
            "timestamp": row[4],
        }
        for row in flask.g.syscnx.execute(sql, (user["username"],))
    ]
    return flask.render_template("user/logs.html", user=user, logs=logs)


@blueprint.route("/users")
@utils.admin_required
def users():
    "Display list of all users."
    return flask.render_template("user/users.html", users=get_all_users())


@blueprint.route("/enable/<name:username>", methods=["POST"])
@utils.admin_required
def enable(username):
    "Enable the given user account."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("no such user")
        return flask.redirect(flask.url_for("home"))
    with UserSaver(user) as ctx:
        ctx.set_status(constants.ENABLED)
    return flask.redirect(flask.url_for(".display", username=username))


@blueprint.route("/disable/<name:username>", methods=["POST"])
@utils.admin_required
def disable(username):
    "Disable the given user account."
    user = get_user(username=username)
    if user is None:
        utils.flash_error("no such user")
        return flask.redirect(flask.url_for("home"))
    with UserSaver(user) as ctx:
        ctx.set_status(constants.DISABLED)
    return flask.redirect(flask.url_for(".display", username=username))


class UserSaver:
    "Context for creating, modifying and saving a user account."

    def __init__(self, user=None):
        if user is None:
            self.user = {
                "status": constants.ENABLED,
                "quota": flask.current_app.config["USER_DEFAULT_QUOTA"],
                "created": utils.get_time(),
            }
            self.orig = {}
        else:
            self.user = user
            self.orig = user.copy()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None:
            return False
        for key in ["username", "email", "role", "status"]:
            if not self.user.get(key):
                raise ValueError("invalid user: %s not set" % key)
        self.user["modified"] = utils.get_time()
        cnx = utils.get_cnx(write=True)
        rows = cnx.execute(
            "SELECT COUNT(*) FROM users WHERE username=?", (self.user["username"],)
        ).fetchall()
        with cnx:
            # Update user
            if rows[0][0]:
                sql = (
                    "UPDATE users SET email=?, password=?,"
                    " apikey=?, role=?, status=?, quota=?, modified=?"
                    " WHERE username=?"
                )
                cnx.execute(
                    sql,
                    (
                        self.user["email"],
                        self.user["password"],
                        self.user.get("apikey"),
                        self.user["role"],
                        self.user["status"],
                        self.user["quota"],
                        self.user["modified"],
                        self.user["username"],
                    ),
                )
            # Add user
            else:
                sql = (
                    "INSERT INTO users"
                    " (username, email, password, apikey, role,"
                    "  status, quota, created, modified)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                )
                cnx.execute(
                    sql,
                    (
                        self.user["username"],
                        self.user["email"],
                        self.user["password"],
                        self.user.get("apikey"),
                        self.user["role"],
                        self.user["status"],
                        self.user["quota"],
                        self.user["created"],
                        self.user["modified"],
                    ),
                )
            # Add log entry
            new = {}
            for key, value in self.user.items():
                if value != self.orig.get(key):
                    new[key] = value
            new.pop("modified")
            try:
                password = new["password"]
            except KeyError:
                pass
            else:
                if not password.startswith("code:"):
                    new["password"] = "***"
            try:
                if flask.g.current_user:
                    editor = flask.g.current_user["username"]
                else:
                    editor = None
            except AttributeError:
                editor = None
            if flask.has_request_context():
                remote_addr = str(flask.request.remote_addr)
                user_agent = str(flask.request.user_agent)
            else:
                remote_addr = None
                user_agent = None
            sql = (
                "INSERT INTO users_logs (username, new, editor,"
                " remote_addr, user_agent, timestamp)"
                " VALUES (?, ?, ?, ?, ?, ?)"
            )
            cnx.execute(
                sql,
                (
                    self.user["username"],
                    json.dumps(new, ensure_ascii=False),
                    editor,
                    remote_addr,
                    user_agent,
                    utils.get_time(),
                ),
            )

    def set_username(self, username):
        if "username" in self.user:
            raise ValueError("username cannot be changed")
        if not constants.NAME_RX.match(username):
            raise ValueError("invalid username; must be an name")
        if get_user(username=username):
            raise ValueError("username already in use")
        self.user["username"] = username

    def set_email(self, email):
        if not constants.EMAIL_RX.match(email):
            raise ValueError("invalid email")
        if get_user(email=email):
            raise ValueError("email already in use")
        self.user["email"] = email

    def set_status(self, status):
        if status not in constants.USER_STATUSES:
            raise ValueError("invalid status")
        self.user["status"] = status

    def set_quota(self, quota):
        if quota is not None and quota <= 0:
            quota = flask.current_app.config["USER_DEFAULT_QUOTA"]
        self.user["quota"] = quota

    def set_role(self, role):
        if role not in constants.USER_ROLES:
            raise ValueError("invalid role")
        self.user["role"] = role

    def set_password(self, password):
        "Set the password."
        config = flask.current_app.config
        if len(password) < config["MIN_PASSWORD_LENGTH"]:
            raise ValueError("password too short")
        self.user["password"] = werkzeug.security.generate_password_hash(
            password, salt_length=config["SALT_LENGTH"]
        )

    def set_apikey(self):
        "Set a new API key."
        self.user["apikey"] = utils.get_iuid()


# Utility functions


def get_user(username=None, email=None, apikey=None):
    """Return the user for the given username, email or apikey.
    Return None if no such user.
    """
    print(username, email, apikey)
    if username:
        name = username
        criterion = " WHERE username=?"
    elif email:
        name = email
        criterion = " WHERE email=?"
    elif apikey:
        name = apikey
        criterion = " WHERE apikey=?"
    else:
        return None
    sql = (
        "SELECT username, email, password, apikey, role, status,"
        " quota, created, modified FROM users" + criterion
    )
    rows = flask.g.syscnx.execute(sql, (name,)).fetchall()
    if len(rows) != 1:
        return None  # 'rowcount' does not work?!
    return dict(rows[0])


def get_current_user():
    """Return the user for the current session.
    Return None if no such user, or disabled.
    """
    user = get_user(
        username=flask.session.get("username"),
        apikey=flask.request.headers.get("x-apikey"),
    )
    if user is None:
        return None
    if user["status"] == constants.ENABLED:
        return user
    else:
        flask.session.pop("username", None)
        return None


def is_admin_or_self(user):
    "Is the current user admin, or the same as the given user?"
    if not flask.g.current_user:
        return False
    if flask.g.is_admin:
        return True
    return flask.g.current_user["username"] == user["username"]


def is_admin_and_not_self(user):
    "Is the current user admin, but not the same as the given user?"
    if flask.g.is_admin:
        return flask.g.current_user["username"] != user["username"]
    return False


def get_all_users():
    "Return a list of all users."
    import dbshare.dbs

    sql = (
        "SELECT username, email, password, apikey,"
        " role, status, quota, created, modified FROM users"
    )
    users = [dict(row) for row in flask.g.syscnx.execute(sql)]
    for user in users:
        user["ndbs"] = 0
        user["size"] = 0
    lookup = dict([(u["username"], u) for u in users])
    for db in dbshare.dbs.get_dbs():
        lookup[db["owner"]]["ndbs"] += 1
        lookup[db["owner"]]["size"] += db["size"]
    return users
