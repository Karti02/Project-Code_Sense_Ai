#!/usr/bin/env python3
"""
Standalone administrator setup script.

Use this if `flask create-admin` isn't being picked up in your environment
(most commonly: the "flask" CLI not resolving app/cli.py, wrong working
directory, or a stale virtualenv). This script does the exact same thing
directly, with no dependency on Flask's CLI/command discovery.

Usage:
    cd codesense-ai              # the folder containing this file and run.py
    ADMIN_PASSWORD='a-long-random-passphrase' python create_admin.py --username admin --email admin@example.com

    # or, to be prompted securely instead of using an env var:
    python create_admin.py --username admin --email admin@example.com

The password is never hard-coded here or anywhere in the codebase - it
must come from the ADMIN_PASSWORD environment variable, or a hidden
getpass prompt if that variable isn't set.
"""

import os
import sys
import getpass
import argparse

# Make sure this script can be run from the project root regardless of
# how it's invoked.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User


def main():
    parser = argparse.ArgumentParser(description="Create or promote an administrator account.")
    parser.add_argument("--username", default=os.environ.get("ADMIN_USERNAME"))
    parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL"))
    args = parser.parse_args()

    username = args.username or input("Admin username: ").strip()
    email = (args.email or input("Admin email: ").strip()).lower()

    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Admin password (hidden, not stored in shell history): ")
        confirm = getpass.getpass("Confirm admin password: ")
        if password != confirm:
            print("Passwords do not match. Aborting.", file=sys.stderr)
            sys.exit(1)

    if not password or len(password) < 12:
        print(
            "Refusing to create an admin with a weak/empty password. "
            "Use at least 12 characters (set ADMIN_PASSWORD or enter one when prompted).",
            file=sys.stderr,
        )
        sys.exit(1)

    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        db.create_all()

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            existing.role = "admin"
            if os.environ.get("ADMIN_RESET_PASSWORD") == "1":
                existing.set_password(password)
            db.session.commit()
            print(f"Existing user '{existing.username}' promoted to admin.")
            return

        admin = User(username=username, email=email, full_name=username, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Administrator '{username}' created successfully.")


if __name__ == "__main__":
    main()
