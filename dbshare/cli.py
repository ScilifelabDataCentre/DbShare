"Command line interface to the DbShare instance."

import json
import os.path

import click
import flask

import dbshare.app
import dbshare.dbs
import dbshare.api.db
import dbshare.system
import dbshare.user

from dbshare import constants
from dbshare import utils


@click.group()
def cli():
    "Command line interface for operations on the DbShare instance."
    pass


@cli.command()
def counts():
    "Output counts of databases and users."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        dbs = dbshare.dbs.get_dbs()
        click.echo(f"{len(dbs)} databases.")
        users = dbshare.user.get_all_users()
        click.echo(f"{len(users)} users.")


@cli.command()
@click.option("--username", help="Username for the new admin account.", prompt=True)
@click.option("--email", help="Email address for the new admin account.", prompt=True)
@click.option(
    "--password",
    help="Password for the new admin account.",
    prompt=True,
    hide_input=True,
)
def create_admin(username, email, password):
    "Create a new admin account."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        try:
            with dbshare.user.UserSaver() as saver:
                saver.set_username(username)
                saver.set_email(email)
                saver.set_password(password)
                saver.set_role(constants.ADMIN)
                saver.set_status(constants.ENABLED)
        except ValueError as error:
            raise click.ClickException(str(error))


@cli.command()
@click.option("--username", help="Username for the new user account.", prompt=True)
@click.option("--email", help="Email address for the new user account.", prompt=True)
@click.option(
    "--password",
    help="Password for the new user account.",
    prompt=True,
    hide_input=True,
)
def create_user(username, email, password):
    "Create a new user account."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        try:
            with dbshare.user.UserSaver() as saver:
                saver.set_username(username)
                saver.set_email(email)
                saver.set_password(password)
                saver.set_role(constants.USER)
                saver.set_status(constants.ENABLED)
        except ValueError as error:
            raise click.ClickException(str(error))


@cli.command()
@click.option("--username", help="Username for the user account.", prompt=True)
@click.option(
    "--password",
    help="New password for the user account.",
    prompt=True,
    hide_input=True,
)
def password(username, password):
    "Set the password for a user account."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        user = dbshare.user.get_user(username)
        if user:
            with dbshare.user.UserSaver(user) as saver:
                saver.set_password(password)
        else:
            raise click.ClickException("No such user.")


@cli.command()
def users():
    "Output list of users."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        for user in dbshare.user.get_all_users():
            click.echo(user["username"])


@cli.command()
@click.argument("username")
def user(username):
    "Show the JSON for the named user."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        click.echo(json.dumps(dbshare.user.get_user(username), indent=2))


@cli.command()
def dbs():
    "Output list of databases."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        for db in dbshare.dbs.get_dbs():
            click.echo(db["name"])


@cli.command()
@click.argument("dbname")
@click.argument("username")
@click.option(
    "-d",
    "--dbfile",
    type=str,
    default=None,
    help="The path of the DbShare Sqlite3 database file.",
)
def create_db(dbname, username, dbfile):
    "Create a new database, optionally from a DbShare Sqlite3 database file."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        try:
            user = dbshare.user.get_user(username=username)
            if user is None:
                raise ValueError("No such user.")
            flask.g.current_user = user
            if dbfile:
                size = os.path.getsize(dbfile)
                with open(dbfile, "rb") as infile:
                    db = dbshare.db.add_sqlite3_database(dbname, infile, size)
        except (ValueError, IOError) as error:
            raise click.ClickException(str(error))
    click.echo(f"Created database {dbname}.")


@cli.command()
@click.argument("name")
def db(name):
    "Show the JSON for the named database."
    with dbshare.app.app.app_context():
        flask.g.syscnx = utils.get_cnx()
        db = dbshare.db.get_db(name, complete=True)
        if db is None:
            raise click.ClickException("No such database.")
        click.echo(
            json.dumps(
                dbshare.api.db.get_json(db, complete=True), ensure_ascii=False, indent=2
            )
        )

@cli.command()
def dump():
    raise NotImplementedError


@cli.command()
def undump():
    raise NotImplementedError


if __name__ == "__main__":
    cli()
