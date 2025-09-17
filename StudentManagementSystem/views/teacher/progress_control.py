from django.contrib import messages
from django.shortcuts import render, redirect
from GameProgress.models import LevelDefinition, AchievementDefinition, LevelProgress, AchievementProgress
from GameProgress.services.progress_teacher import (
    sync_students_progress,
    unlock_levels_for_students,
    lock_levels_for_students,
    enable_all_achievements_for_students,
    disable_all_achievements_for_students,
    reset_progress_for_students,
    set_achievement_active_for_students,
)
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.views.teacher.dashboard_teacher import get_teacher_dashboard_context


def _get_students_for_action(handled_sections, section_id=None):
    """Return only the students for this teacher, optionally filtered by section."""
    if section_id:
        return Student.objects.filter(section_id=section_id)
    return Student.objects.filter(section_id__in=handled_sections.values_list("section_id", flat=True))


@session_login_required(role=Role.TEACHER)
def progress_control_teacher(request):
    teacher = request.user_obj
    handled_sections = teacher.handled_sections.select_related("department", "year_level", "section")

    if request.method == "POST":
        action = request.POST.get("action")
        section_id = request.POST.get("section_id") or None
        level_name = request.POST.get("level_name")
        achievement_code = request.POST.get("achievement_code")

        students = _get_students_for_action(handled_sections, section_id)

        if action == "sync":
            sync_students_progress(students)
            messages.success(request, "✅ Synced students with current definitions.")

        elif action == "unlock_levels":
            unlock_levels_for_students(students)
            messages.success(request, "✅ Levels unlocked.")

        elif action == "lock_levels":
            lock_levels_for_students(students)
            messages.success(request, "🔒 Levels locked.")

        elif action == "enable_achievements":
            enable_all_achievements_for_students(students)
            messages.success(request, "✅ Achievements enabled.")

        elif action == "disable_achievements":
            disable_all_achievements_for_students(students)
            messages.success(request, "🔒 Achievements disabled.")

        elif action == "reset_progress":
            reset_progress_for_students(students)
            messages.warning(request, "⚠️ Progress reset.")

        elif action == "disable_single_achievement" and achievement_code:
            set_achievement_active_for_students(students, achievement_code, False)
            messages.info(request, f"🔒 Achievement '{achievement_code}' disabled.")

        elif action == "enable_single_achievement" and achievement_code:
            set_achievement_active_for_students(students, achievement_code, True)
            messages.info(request, f"✅ Achievement '{achievement_code}' enabled.")

        elif action == "lock_single_level" and level_name:
            lock_levels_for_students(students, level_name=level_name)
            messages.info(request, f"🔒 Level '{level_name}' locked.")

        elif action == "unlock_single_level" and level_name:
            unlock_levels_for_students(students, level_name=level_name)
            messages.info(request, f"✅ Level '{level_name}' unlocked.")

        # 🔹 Global single-level / single-achievement actions
        elif action == "lock_single_level_global" and level_name:
            lock_levels_for_students(_get_students_for_action(handled_sections), level_name=level_name)
            messages.info(request, f"🔒 Level '{level_name}' locked for ALL your sections.")

        elif action == "unlock_single_level_global" and level_name:
            unlock_levels_for_students(_get_students_for_action(handled_sections), level_name=level_name)
            messages.info(request, f"✅ Level '{level_name}' unlocked for ALL your sections.")

        elif action == "disable_single_achievement_global" and achievement_code:
            set_achievement_active_for_students(_get_students_for_action(handled_sections), achievement_code, False)
            messages.info(request, f"🔒 Achievement '{achievement_code}' disabled for ALL your sections.")

        elif action == "enable_single_achievement_global" and achievement_code:
            set_achievement_active_for_students(_get_students_for_action(handled_sections), achievement_code, True)
            messages.info(request, f"✅ Achievement '{achievement_code}' enabled for ALL your sections.")

        return redirect("progress_control_teacher")

    # 📌 Reload fresh status after POST
    all_levels = list(LevelDefinition.objects.all())
    all_achievements = list(AchievementDefinition.objects.all())

    for hs in handled_sections:
        students = Student.objects.filter(section_id=hs.section_id)

        # Annotate definitions with progress
        levels_with_status = []
        for lvl in all_levels:
            unlocked = LevelProgress.objects.filter(
                student__in=students, level=lvl, unlocked=True
            ).exists()
            levels_with_status.append({
                "name": lvl.name,
                "unlocked": unlocked,
            })

        achievements_with_status = []
        for ach in all_achievements:
            active = AchievementProgress.objects.filter(
                student__in=students, achievement=ach, is_active=True
            ).exists()
            achievements_with_status.append({
                "code": ach.code,
                "title": ach.title,
                "is_active": active,
            })

        hs.levels = levels_with_status
        hs.achievements = achievements_with_status

    context = get_teacher_dashboard_context(teacher)
    context["handled_sections"] = handled_sections
    context["all_levels"] = all_levels
    context["all_achievements"] = all_achievements
    return render(request, "teacher/main/progress_control.html", context)
