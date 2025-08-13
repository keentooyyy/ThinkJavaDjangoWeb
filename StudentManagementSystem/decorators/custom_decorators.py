from functools import wraps
from django.shortcuts import redirect

def session_login_required(role=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.session.get('user_id')
            user_role = request.session.get('role')

            if not user_id or (role and user_role != role):
                return redirect('unified_login')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
