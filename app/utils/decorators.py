

from functools import wraps

from flask import abort, redirect, url_for, flash, request
from flask_login import current_user


def admin_required(view_func):
    """
    Restrict a route to authenticated users with the "admin" role.

    - Anonymous users are redirected to the login page (with ?next= set),
      same as @login_required, so admin URLs don't leak their existence
      to logged-out visitors via a distinct status code.
    - Authenticated non-admin users get a 403.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.url))
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped
