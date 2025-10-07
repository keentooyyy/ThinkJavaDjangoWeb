from datetime import datetime
from django.utils import timezone, formats
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse

from GameProgress.models import LevelDefinition, AchievementDefinition, LevelProgress, AchievementProgress
from GameProgress.services.progress_teacher import (
    unlock_levels_for_students,
    lock_levels_for_students,
    enable_all_achievements_for_students,
    disable_all_achievements_for_students,
    set_achievement_active_for_students,
    unlock_level_with_schedule,
)
from StudentManagementSystem.decorators.custom_decorators import session_login_required
from StudentManagementSystem.models import Student
from StudentManagementSystem.models.roles import Role
from StudentManagementSystem.views.notifications_helper import create_notification
from StudentManagementSystem.views.teacher.dashboard_teacher import get_teacher_dashboard_context



# --------------------
# 🔹 Helpers
# --------------------
def _get_students_for_action(handled_sections, section_id=None):
    """Return only the students for this teacher, optionally filtered by section."""
    if section_id:
        if handled_sections.filter(section_id=section_id).exists():
            return Student.objects.filter(section_id=section_id)
        return Student.objects.none()
    return Student.objects.filter(section_id__in=handled_sections.values_list("section_id", flat=True))


def _parse_schedule_dates(start_date, due_date):
    """Parse string dates into aware datetimes and validate order."""
    fmt = "%Y-%m-%d %H:%M:%S"
    local_tz = timezone.get_current_timezone()

    def parse(dt_str):
        if not dt_str:
            return None
        dt = datetime.strptime(dt_str, fmt)
        return timezone.make_aware(dt, local_tz)

    start_dt = parse(start_date)
    due_dt = parse(due_date)

    def fmt_dt(dt):
        return formats.date_format(dt, "M d, Y h:i A")  # e.g. "Sep 18, 2025 08:00 AM"

    # Validation
    if start_dt and due_dt:
        if due_dt < start_dt:
            raise ValueError(
                f"Invalid schedule: Due date/time ({fmt_dt(due_dt)}) "
                f"is earlier than start date/time ({fmt_dt(start_dt)})."
            )
        if start_dt.date() == due_dt.date() and due_dt <= start_dt:
            raise ValueError(
                f"Invalid schedule: On {fmt_dt(start_dt).split()[0]}, "
                f"due time ({due_dt.strftime('%I:%M %p')}) "
                f"cannot be earlier than or equal to start time ({start_dt.strftime('%I:%M %p')})."
            )

    return start_dt, due_dt


def _notify_students_level_unlocked(request, students, level_name, due_dt=None):
    """
    Send notifications to students when a level is unlocked.
    """
    for student in students:
        message = f"Your teacher has unlocked level '{level_name}'."
        if due_dt:
            message += f" Due date: {due_dt.strftime('%b %d, %Y %I:%M %p')}."
        create_notification(
            request,
            recipient_role=Role.STUDENT,
            title="Level Unlocked",
            message=message,
            student_recipient=student
        )


def _attach_section_progress(section, students, all_levels, all_achievements):
    """Annotate a section with its levels and achievements progress."""
    section.levels = [
        {"name": lvl.name,
         "unlocked": LevelProgress.objects.filter(student__in=students, level=lvl, unlocked=True).exists()}
        for lvl in all_levels
    ]
    section.achievements = [
        {"code": ach.code, "title": ach.title,
         "is_active": AchievementProgress.objects.filter(student__in=students, achievement=ach,
                                                         is_active=True).exists()}
        for ach in all_achievements
    ]
    return section


from GameProgress.models.level_schedule import SectionLevelSchedule

def _handle_post_action(
    request,
    action,
    students,
    handled_sections,
    level_name=None,
    achievement_code=None,
    section_id=None,
    start_date=None,
    due_date=None,
):
    """Handle teacher progress actions and return (msg_type, msg_text)."""

    # helper: resolve section label safely
    section_label = None
    if section_id and handled_sections.filter(section_id=section_id).exists():
        hs = handled_sections.get(section_id=section_id)
        section_label = f"{hs.section.department.name}{hs.section.year_level.year}{hs.section.letter}"

    scope = f"for section {section_label}" if section_label else "for your handled sections"

    def result(msg, danger=False):
        return ("error" if danger else "success", msg)

    # 🔹 Helper: clear conflicting schedules when teacher manually overrides lock/unlock
    def clear_conflicting_schedules(level_name=None):
        section_ids = students.values_list("section_id", flat=True).distinct()
        filters = {"section_id__in": section_ids}
        if level_name:
            filters["level__name"] = level_name
        deleted = SectionLevelSchedule.objects.filter(**filters).delete()
        # print(f"[SCHEDULE CLEANUP] Removed {deleted[0]} conflicting schedule entries", flush=True)

    # ----------------------------
    # 🔹 Manual Level Actions
    # ----------------------------
    if action == "unlock_levels":
        clear_conflicting_schedules()
        unlock_levels_for_students(students)
        _notify_students_level_unlocked(request, students, "All Levels")
        return result(f"All levels have been unlocked {scope}.")

    if action == "lock_levels":
        clear_conflicting_schedules()
        lock_levels_for_students(students)
        return result(f"All levels have been locked {scope}.", danger=True)

    # ----------------------------
    # 🔹 Manual Achievement Actions
    # ----------------------------
    if action == "enable_achievements":
        enable_all_achievements_for_students(students)
        return result(f"All achievements are now enabled {scope}.")

    if action == "disable_achievements":
        disable_all_achievements_for_students(students)
        return result(f"All achievements have been disabled {scope}.", danger=True)

    if action in ("disable_single_achievement", "enable_single_achievement") and achievement_code:
        is_active = action == "enable_single_achievement"
        set_achievement_active_for_students(students, achievement_code, is_active)
        state = "enabled" if is_active else "disabled"
        return result(f"Achievement '{achievement_code}' has been {state} {scope}.", danger=not is_active)

    # ----------------------------
    # 🔹 Single Level Lock/Unlock
    # ----------------------------
    if action in ("lock_single_level", "unlock_single_level") and level_name:
        is_unlock = action == "unlock_single_level"
        clear_conflicting_schedules(level_name)

        if is_unlock:
            unlock_levels_for_students(students, level_name=level_name)
            _notify_students_level_unlocked(request, students, level_name)
            return result(f"Level '{level_name}' has been unlocked {scope}.")
        else:
            lock_levels_for_students(students, level_name=level_name)
            return result(f"Level '{level_name}' has been locked {scope}.", danger=True)

    # ----------------------------
    # 🔹 Scheduled Unlock (keeps schedule)
    # ----------------------------
    if action == "unlock_single_level_with_schedule" and level_name and section_id:
        if handled_sections.filter(section_id=section_id).exists():
            section = handled_sections.get(section_id=section_id).section

            try:
                start_dt, due_dt = _parse_schedule_dates(start_date, due_date)
            except ValueError as e:
                return "error", str(e)

            success, msg = unlock_level_with_schedule(
                students,
                level_name=level_name,
                section=section,
                start_date=start_dt,
                due_date=due_dt,
            )

            if success:
                _notify_students_level_unlocked(request, students, level_name, due_dt)

            return ("success" if success else "error", msg)

    # ----------------------------
    # 🔹 Global Actions
    # ----------------------------
    global_students = _get_students_for_action(handled_sections)

    if action in ("lock_single_level_global", "unlock_single_level_global") and level_name:
        is_unlock = action == "unlock_single_level_global"
        clear_conflicting_schedules(level_name)

        if is_unlock:
            unlock_levels_for_students(global_students, level_name=level_name)
            _notify_students_level_unlocked(request, global_students, level_name)
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

        start_date = request.POST.get("start_date")
        due_date = request.POST.get("due_date")

        students = _get_students_for_action(handled_sections, section_id)
        msg_type, msg_text = _handle_post_action(
            request, action, students, handled_sections,
            level_name, achievement_code, section_id,
            start_date=start_date, due_date=due_date
        )

        if msg_text:
            if msg_type == "error":
                messages.error(request, msg_text, extra_tags=extra_tags)
            else:
                messages.success(request, msg_text, extra_tags=extra_tags)

        # ✅ Preserve filter_by param safely
        filter_by = request.GET.get("filter_by") or section_id
        if filter_by and not handled_sections.filter(section_id=filter_by).exists():
            filter_by = None

        redirect_url = reverse("progress_control_teacher")
        if filter_by:
            redirect_url += f"?filter_by={filter_by}"

        return redirect(redirect_url)

    # ---------------- GET ----------------
    all_levels = list(LevelDefinition.objects.all())
    all_achievements = list(AchievementDefinition.objects.all())

    sections = [hs.section for hs in handled_sections]
    departments = {hs.section.department for hs in handled_sections}
    selected_section = request.GET.get("filter_by")

    if selected_section and not handled_sections.filter(section_id=selected_section).exists():
        selected_section = None

    if not selected_section and sections:
        first_section = sections[0]
        return redirect(f"{reverse('progress_control_teacher')}?filter_by={first_section.id}")

    selected_section_obj = next((s for s in sections if str(s.id) == str(selected_section)), None)

    if selected_section_obj:
        students = Student.objects.filter(section_id=selected_section_obj.id)
        selected_section_obj = _attach_section_progress(selected_section_obj, students, all_levels, all_achievements)

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

            # ⏰ for modal dropdowns
            "hours": list(range(1, 13)),  # 1–12
            "minutes": [f"{i:02d}" for i in range(0, 60, 5)],  # 00–59 step 5
        }
    )

    return render(request, "teacher/main/progress_control.html", context)
