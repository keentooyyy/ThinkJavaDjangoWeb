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


# --------------------
# 🔹 Helpers
# --------------------
def _get_students_for_action(handled_sections, section_id=None):
    """Return only the students for this teacher, optionally filtered by section."""
    if section_id:
        return Student.objects.filter(section_id=section_id)
    return Student.objects.filter(section_id__in=handled_sections.values_list("section_id", flat=True))


def _handle_post_action(action, students, handled_sections, level_name=None, achievement_code=None, section_id=None):
    """Handle teacher progress actions and return (msg_type, msg_text)."""

    # helper: resolve section label
    section_label = None
    if section_id:
        section_obj = next((hs.section for hs in handled_sections if str(hs.section.id) == str(section_id)), None)
        if section_obj:
            section_label = f"{section_obj.department.name}{section_obj.year_level.year}{section_obj.letter}"

    # determine scope
    scope = f"for section {section_label}" if section_label else "for your handled sections"

    # ✅ Always default to success unless specified as danger
    def result(msg, danger=False):
        return ("error" if danger else "success", msg)

    if action == "sync":
        sync_students_progress(students)
        return result(f"All student progress has been synced {scope}.")

    if action == "unlock_levels":
        unlock_levels_for_students(students)
        return result(f"All levels have been unlocked {scope}.")

    if action == "lock_levels":
        lock_levels_for_students(students)
        return result(f"All levels have been locked {scope}.", danger=True)

    if action == "enable_achievements":
        enable_all_achievements_for_students(students)
        return result(f"All achievements are now enabled {scope}.")

    if action == "disable_achievements":
        disable_all_achievements_for_students(students)
        return result(f"All achievements have been disabled {scope}.", danger=True)

    if action == "reset_progress":
        reset_progress_for_students(students)
        return result(f"All student progress has been reset {scope}.", danger=True)

    if action in ("disable_single_achievement", "enable_single_achievement") and achievement_code:
        is_active = action == "enable_single_achievement"
        set_achievement_active_for_students(students, achievement_code, is_active)
        state = "enabled" if is_active else "disabled"
        return result(
            f"Achievement '{achievement_code}' has been {state} {scope}.",
            danger=not is_active,
        )

    if action in ("lock_single_level", "unlock_single_level") and level_name:
        is_unlock = action == "unlock_single_level"
        if is_unlock:
            unlock_levels_for_students(students, level_name=level_name)
            return result(f"Level '{level_name}' has been unlocked {scope}.")
        else:
            lock_levels_for_students(students, level_name=level_name)
            return result(f"Level '{level_name}' has been locked {scope}.", danger=True)

    # 🔹 Global single-level / single-achievement actions
    global_students = _get_students_for_action(handled_sections)
    if action in ("lock_single_level_global", "unlock_single_level_global") and level_name:
        is_unlock = action == "unlock_single_level_global"
        if is_unlock:
            unlock_levels_for_students(global_students, level_name=level_name)
            return result(f"Level '{level_name}' has been unlocked across all your handled sections.")
        else:
            lock_levels_for_students(global_students, level_name=level_name)
            return result(f"Level '{level_name}' has been locked across all your handled sections.", danger=True)

    if action in ("disable_single_achievement_global", "enable_single_achievement_global") and achievement_code:
        is_active = action == "enable_single_achievement_global"
        set_achievement_active_for_students(global_students, achievement_code, is_active)
        state = "enabled" if is_active else "disabled"
        return result(
            f"Achievement '{achievement_code}' has been {state} across all your handled sections.",
            danger=not is_active,
        )

    return "error", "Unknown action. Please try again."


def _attach_section_progress(section, students, all_levels, all_achievements):
    """Annotate a section with its levels and achievements progress."""
    levels_with_status = [
        {
            "name": lvl.name,
            "unlocked": LevelProgress.objects.filter(student__in=students, level=lvl, unlocked=True).exists(),
        }
        for lvl in all_levels
    ]

    achievements_with_status = [
        {
            "code": ach.code,
            "title": ach.title,
            "is_active": AchievementProgress.objects.filter(student__in=students, achievement=ach, is_active=True).exists(),
        }
        for ach in all_achievements
    ]

    section.levels = levels_with_status
    section.achievements = achievements_with_status
    return section


# --------------------
# 🔹 Main View
# --------------------
@session_login_required(role=Role.TEACHER)
def progress_control_teacher(request):
    extra_tags = "control_messages"
    teacher = request.user_obj
    handled_sections = teacher.handled_sections.select_related("department", "year_level", "section")

    # ---------------- POST ----------------
    if request.method == "POST":
        action = request.POST.get("action")
        section_id = request.POST.get("section_id") or None
        level_name = request.POST.get("level_name")
        achievement_code = request.POST.get("achievement_code")

        students = _get_students_for_action(handled_sections, section_id)
        msg_type, msg_text = _handle_post_action(
            action,
            students,
            handled_sections,
            level_name,
            achievement_code,
            section_id,  # <-- add this
        )

        if msg_text:
            # ✅ Always success unless explicitly error
            if msg_type == "error":
                messages.error(request, msg_text, extra_tags=extra_tags)
            else:
                messages.success(request, msg_text, extra_tags=extra_tags)

        return redirect("progress_control_teacher")

    # ---------------- GET ----------------
    all_levels = list(LevelDefinition.objects.all())
    all_achievements = list(AchievementDefinition.objects.all())

    # Filters
    sections = [hs.section for hs in handled_sections]
    departments = {hs.section.department for hs in handled_sections}
    selected_section = request.GET.get("filter_by")
    selected_section_obj = None

    if selected_section:
        selected_section_obj = next((s for s in sections if str(s.id) == selected_section), None)

    if selected_section_obj:
        students = Student.objects.filter(section_id=selected_section_obj.id)
        selected_section_obj = _attach_section_progress(selected_section_obj, students, all_levels, all_achievements)

    # Context
    context = get_teacher_dashboard_context(teacher)
    context.update(
        {
            "handled_sections": handled_sections,
            "all_levels": all_levels,
            "all_achievements": all_achievements,
            "departments": departments,
            "sections": sections,
            "selected_section": selected_section,
            "selected_section_obj": selected_section_obj,
        }
    )

    return render(request, "teacher/main/progress_control.html", context)
