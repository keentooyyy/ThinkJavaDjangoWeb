# views.py
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count

from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student, Teacher, SimpleAdmin
from StudentManagementSystem.models.roles import Role
from GameProgress.models import AchievementDefinition, LevelDefinition
from GameProgress.services.ranking import get_section_rankings
from StudentManagementSystem.models.section import Section


@session_login_required(Role.ADMIN)
def admin_dashboard(request):
    """
    Render the dashboard shell only (with spinners).
    Data will be loaded asynchronously via AJAX.
    """
    user_id = request.session.get('user_id')
    admin = SimpleAdmin.objects.get(id=user_id)

    username= admin.username
    role = admin.role


    context = {
        'username': username,
        'role': role,
    }
    return render(request, "admin/dashboard.html", context)


@session_login_required(Role.ADMIN)
def dashboard_students(request):
    total = Student.objects.count()
    cs = Student.objects.filter(section__department_id=1).count()
    it = Student.objects.filter(section__department_id=2).count()
    return JsonResponse({
        "student_count": total,
        "student_count_CS": cs,
        "student_count_IT": it,
    })


@session_login_required(Role.ADMIN)
def dashboard_teachers(request):
    return JsonResponse({
        "teacher_count": Teacher.objects.count()
    })


@session_login_required(Role.ADMIN)
def dashboard_sections(request):
    return JsonResponse({
        "section_count": Section.objects.count()
    })


@session_login_required(Role.ADMIN)
def dashboard_ranking(request):
    return JsonResponse({
        "ranking_by_section": get_section_rankings()
    })


@session_login_required(Role.ADMIN)
def dashboard_progress(request):
    return JsonResponse({
        "achievements_count": AchievementDefinition.objects.count(),
        "levels_count": LevelDefinition.objects.count(),
        "achievements": list(AchievementDefinition.objects.values(
            "id", "code", "title", "is_active"
        )),
        "levels": list(LevelDefinition.objects.values(
            "id", "name", "unlocked"
        )),
    })
