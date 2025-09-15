from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import UserProfile
from StudentManagementSystem.models.roles import Role


@session_login_required(role=[Role.ADMIN, Role.STUDENT, Role.TEACHER])
def edit_profile(request):
    role = request.session.get("role")
    user = request.user_obj  # provided by decorator

    # 🔹 Username display logic
    if role in [Role.STUDENT, Role.TEACHER]:
        username = f"{user.first_name} {user.last_name}"
    elif role == Role.ADMIN:
        username = user.username
    else:
        return redirect("unified_login")

    # 🔹 Fetch or create linked UserProfile
    content_type = ContentType.objects.get_for_model(user)
    profile, _ = UserProfile.objects.get_or_create(
        content_type=content_type,
        object_id=user.id
    )

    return render(request, "edit_profile.html", {
        "user": user,
        "profile": profile,
        "role": role,
        "username": username,
    })
