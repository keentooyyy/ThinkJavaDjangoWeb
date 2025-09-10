from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse


def session_login_required(role=None):
    """
    For browser views:
    - Redirects to 'unified_logout' if no session or role mismatch
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.session.get("user_id")
            user_role = request.session.get("role")

            allowed_roles = role if isinstance(role, (list, tuple, set)) else [role] if role else []

            if not user_id or (allowed_roles and user_role not in allowed_roles):
                return redirect("unified_logout")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
