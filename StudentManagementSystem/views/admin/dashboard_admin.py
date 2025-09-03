from django.http import JsonResponse
from django.shortcuts import render

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student, Teacher, SimpleAdmin
from StudentManagementSystem.models.roles import Role
from GameProgress.models import AchievementDefinition, LevelDefinition
from GameProgress.services.ranking import get_section_rankings
from StudentManagementSystem.models.section import Section


@session_login_required(Role.ADMIN)
def admin_dashboard(request):
    """
    Render the dashboard with context (fast queries only).
    Ranking is fetched via AJAX.
    """
    user_id = request.session.get("user_id")
    admin = SimpleAdmin.objects.get(id=user_id)

    context = {
        "username": admin.username,
        "role": admin.role,

        # Students / Teachers / Sections
        "student_count": Student.objects.count(),
        "student_count_CS": Student.objects.filter(section__department_id=1).count(),
        "student_count_IT": Student.objects.filter(section__department_id=2).count(),
        "teacher_count": Teacher.objects.count(),
        "section_count": Section.objects.count(),

        # Levels / Achievements
        "levels_count": LevelDefinition.objects.count(),
        "achievements_count": AchievementDefinition.objects.count(),
        "levels": LevelDefinition.objects.all(),
        "achievements": AchievementDefinition.objects.all(),
    }
    return render(request, "admin/dashboard.html", context)


# --- Only ranking stays async ---
@session_login_required(Role.ADMIN)
def dashboard_ranking(request):
    return JsonResponse({
        "ranking_by_section": get_section_rankings()
    })
