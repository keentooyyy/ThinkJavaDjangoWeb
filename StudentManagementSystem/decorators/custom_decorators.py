from functools import wraps

from django.shortcuts import redirect, get_object_or_404

from StudentManagementSystem.models import Student, Teacher, SimpleAdmin
from StudentManagementSystem.models.roles import Role


def session_login_required(role=None, lookup_kwarg="id"):
    """
    Strict session/role/ownership enforcement for all roles.
    - Verifies user_id + role exist in session.
    - Confirms user exists in DB and session role matches DB role.
    - Enforces ownership if route has a user ID param.
    - Attaches the user object to request.user_obj for safe use in views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            session_user_id = request.session.get("user_id")
            session_role = request.session.get("role")

            allowed_roles = (
                role if isinstance(role, (list, tuple, set))
                else [role] if role else []
            )

            # 🚨 No session or role mismatch → logout
            if not session_user_id or (allowed_roles and session_role not in allowed_roles):
                return redirect("unified_logout")

            # 🚨 DB validation
            if session_role == Role.STUDENT:
                user = get_object_or_404(Student, id=session_user_id)
            elif session_role == Role.TEACHER:
                user = get_object_or_404(Teacher, id=session_user_id)
            elif session_role == Role.ADMIN:
                user = get_object_or_404(SimpleAdmin, id=session_user_id)
            else:
                return redirect("unified_logout")

            # 🚨 Session role must equal DB role
            if user.role != session_role:
                return redirect("unified_logout")

            # 🚨 Ownership validation (if URL carries an id)
            requested_id = kwargs.get(lookup_kwarg)
            if requested_id is not None and str(requested_id) != str(user.id):
                return redirect("unified_logout")

            # ✅ Inject the DB user into the request for safe use
            request.user_obj = user
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
