import os
import getpass

import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User


def register_cli(app):
    app.cli.add_command(create_admin_command)


@click.command("create-admin")
@click.option("--username", default=None, help="Admin username (or set ADMIN_USERNAME env var).")
@click.option("--email", default=None, help="Admin email (or set ADMIN_EMAIL env var).")
@with_appcontext
def create_admin_command(username, email):
    """
    Create (or promote) an administrator account.

    Usage:
        ADMIN_PASSWORD='...' flask create-admin --username admin --email admin@example.com

    If ADMIN_PASSWORD is not set in the environment, you will be prompted
    to enter it securely (input is hidden, nothing is echoed or logged).
    The password is never read from source code or command-line arguments.
    """
    username = username or os.environ.get("ADMIN_USERNAME")
    email = email or os.environ.get("ADMIN_EMAIL")

    if not username:
        username = click.prompt("Admin username")
    if not email:
        email = click.prompt("Admin email")
    email = email.strip().lower()

    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Admin password (hidden, not stored in shell history): ")
        confirm = getpass.getpass("Confirm admin password: ")
        if password != confirm:
            raise click.ClickException("Passwords do not match. Aborting.")

    if not password or len(password) < 12:
        raise click.ClickException(
            "Refusing to create an admin with a weak/empty password. "
            "Use at least 12 characters (set ADMIN_PASSWORD or enter one when prompted)."
        )

    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        existing.role = "admin"
        existing.set_password(password) if os.environ.get("ADMIN_RESET_PASSWORD") == "1" else None
        db.session.commit()
        click.echo(f"Existing user '{existing.username}' promoted to admin.")
        return

    admin = User(username=username, email=email, full_name=username, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Administrator '{username}' created successfully.")
