from functools import wraps

from django.contrib.auth.hashers import check_password
from django.http.response import JsonResponse
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


def api_login_required(role=None, lookup_kwarg="id"):
    """
    API decorator:
    - Reads `student_id` and `password` from request.POST / request.body
    - Confirms user exists and password matches
    - Role restriction (if specified)
    - Injects user into `request.user_obj`
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Extract credentials (works with form-data or JSON body)
            user_id = request.POST.get("student_id") or request.POST.get("user_id")
            password = request.POST.get("password")

            if not user_id or not password:
                return JsonResponse({"error": "Missing credentials"}, status=400)

            # Which roles are allowed?
            allowed_roles = (
                role if isinstance(role, (list, tuple, set))
                else [role] if role else []
            )

            # Try each role type
            user = None
            user_role = None

            for model, role_type in [
                (Student, Role.STUDENT),
                (Teacher, Role.TEACHER),
                (SimpleAdmin, Role.ADMIN),
            ]:
                try:
                    obj = model.objects.get(student_id=user_id)
                    if check_password(password, obj.password):  # assumes hashed pw
                        user = obj
                        user_role = role_type
                        break
                except model.DoesNotExist:
                    continue

            if not user:
                return JsonResponse({"error": "Invalid credentials"}, status=401)

            # Role restriction
            if allowed_roles and user_role not in allowed_roles:
                return JsonResponse({"error": "Insufficient role"}, status=403)

            # Ownership enforcement
            requested_id = kwargs.get(lookup_kwarg)
            if requested_id is not None and str(requested_id) != str(user.id):
                return JsonResponse({"error": "Forbidden"}, status=403)

            # Inject into request
            request.user_obj = user
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
