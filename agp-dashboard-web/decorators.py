from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Restricts access to a route to users with the 'admin' role.
    If the user is not authenticated or not an admin, it flashes an error
    and redirects to the main dashboard.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated and has the is_admin property/method
        if not current_user.is_authenticated or not hasattr(current_user, "is_admin"):
            flash("Debes iniciar sesión para acceder a esta página.", "warning")
            return redirect(
                url_for("auth.login")
            )  # Assuming a login route named 'auth.login'

        # Check if the user is an admin
        if not current_user.is_admin:
            flash("Acceso no autorizado. Se requiere rol de administrador.", "danger")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function
