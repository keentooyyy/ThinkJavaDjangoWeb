from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import UserProfile, EducationalBackground
from StudentManagementSystem.models.roles import Role


def normalize(value):
    """Convert '', 'None', or None to actual Python None (→ DB NULL)."""
    if value in [None, "", "None"]:
        return None
    return value


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
        # --- Update user ---
        user.first_name = normalize(request.POST.get("first_name")) or user.first_name
        user.last_name = normalize(request.POST.get("last_name")) or user.last_name
        user.save()

        # --- Update profile ---
        if "picture" in request.FILES:
            profile.picture = request.FILES["picture"]

        profile.middle_initial = normalize(request.POST.get("middle_initial"))
        profile.suffix = normalize(request.POST.get("suffix"))
        profile.bio = normalize(request.POST.get("bio"))
        profile.date_of_birth = normalize(request.POST.get("date_of_birth"))
        profile.father_name = normalize(request.POST.get("father_name"))
        profile.mother_name = normalize(request.POST.get("mother_name"))
        profile.street = normalize(request.POST.get("street"))
        profile.barangay = normalize(request.POST.get("barangay"))
        profile.city = normalize(request.POST.get("city"))
        profile.province = normalize(request.POST.get("province"))
        profile.phone = normalize(request.POST.get("phone"))
        profile.save()

        # --- Update Educational Background ---
        schools = request.POST.getlist("school[]")
        starts = request.POST.getlist("start_date[]")
        grads = request.POST.getlist("graduation_date[]")

        # Clear existing rows and recreate
        profile.educational_backgrounds.all().delete()

        def parse_year(y):
            """Convert year string into a proper date (YYYY-01-01)."""
            y = normalize(y)
            if not y:
                return None
            try:
                return date(int(y), 1, 1)
            except (ValueError, TypeError):
                return None

        for i in range(len(schools)):
            school = normalize(schools[i])
            if not school:
                continue

            start_date = parse_year(starts[i]) if i < len(starts) else None
            grad_date = parse_year(grads[i]) if i < len(grads) else None

            EducationalBackground.objects.create(
                profile=profile,
                institution=school,
                start_date=start_date,
                graduation_date=grad_date
            )

        return redirect("edit_profile")

    return render(request, "edit_profile.html", {
        "user": user,
        "profile": profile,
        "role": role,
        "username": username,
    })
