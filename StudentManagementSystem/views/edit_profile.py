from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import UserProfile
from StudentManagementSystem.models.roles import Role


@session_login_required(role=[Role.ADMIN, Role.STUDENT, Role.TEACHER])
def edit_profile(request):
    user = request.user_obj
    role = user.role

    if role in [Role.STUDENT, Role.TEACHER]:
        username = f"{user.first_name} {user.last_name}"
    elif role == Role.ADMIN:
        username = user.username
    else:
        return redirect("unified_login")

    content_type = ContentType.objects.get_for_model(user)
    profile, _ = UserProfile.objects.get_or_create(
        content_type=content_type,
        object_id=user.id
    )

    if request.method == "POST":
        # 🔹 Update user fields
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.save()

        # 🔹 Update profile fields
        profile.middle_initial = request.POST.get("middle_initial", profile.middle_initial)
        profile.suffix = request.POST.get("suffix", profile.suffix)
        profile.bio = request.POST.get("bio", profile.bio)
        profile.date_of_birth = request.POST.get("date_of_birth", profile.date_of_birth)
        profile.father_name = request.POST.get("father_name", profile.father_name)
        profile.mother_name = request.POST.get("mother_name", profile.mother_name)

        # 🔹 Address fields
        profile.street = request.POST.get("street", profile.street)
        profile.barangay = request.POST.get("barangay", profile.barangay)
        profile.city = request.POST.get("city", profile.city)
        profile.province = request.POST.get("province", profile.province)
        profile.phone = request.POST.get('phone', profile.phone)

        profile.save()

        return redirect("edit_profile")  # refresh page after save

    return render(request, "edit_profile.html", {
        "user": user,
        "profile": profile,
        "role": role,
        "username": username,
    })
