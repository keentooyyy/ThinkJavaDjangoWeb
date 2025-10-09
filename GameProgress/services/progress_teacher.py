from django.db import transaction

from GameProgress.models import (
    LevelDefinition,
    AchievementDefinition,
    AchievementProgress
)


def sync_students_progress(student_qs):
    """Sync only the given students with all level & achievement definitions."""
    student_ids = list(student_qs.values_list("id", flat=True))
    levels = list(LevelDefinition.objects.values_list("id", flat=True))
    achievements = list(AchievementDefinition.objects.values_list("id", flat=True))

    existing_levels = set(LevelProgress.objects.values_list("student_id", "level_id"))
    existing_achievements = set(AchievementProgress.objects.values_list("student_id", "achievement_id"))

    new_level_progress = []
    new_achievement_progress = []

    for student_id in student_ids:
        for level_id in levels:
            if (student_id, level_id) not in existing_levels:
                new_level_progress.append(
                    LevelProgress(student_id=student_id, level_id=level_id, best_time=0, current_time=0, unlocked=False)
                )
        for achievement_id in achievements:
            if (student_id, achievement_id) not in existing_achievements:
                new_achievement_progress.append(
                    AchievementProgress(student_id=student_id, achievement_id=achievement_id, unlocked=False,
                                        is_active=True)
                )

    with transaction.atomic():
        LevelProgress.objects.bulk_create(new_level_progress, batch_size=1000, ignore_conflicts=True)
        AchievementProgress.objects.bulk_create(new_achievement_progress, batch_size=1000, ignore_conflicts=True)


def unlock_levels_for_students(student_qs, level_name=None):
    qs = LevelProgress.objects.filter(student__in=student_qs)
    if level_name:
        qs = qs.filter(level__name=level_name)
    qs.update(unlocked=True)


def lock_levels_for_students(student_qs, level_name=None):
    qs = LevelProgress.objects.filter(student__in=student_qs)
    if level_name:
        qs = qs.filter(level__name=level_name)
    qs.update(unlocked=False)


def reset_progress_for_students(student_qs):
    LevelProgress.objects.filter(student__in=student_qs).update(best_time=0, current_time=0, unlocked=False)
    AchievementProgress.objects.filter(student__in=student_qs).update(unlocked=False, is_active=True)


def set_achievement_active_for_students(student_qs, achievement_code, active=True):
    AchievementProgress.objects.filter(
        student__in=student_qs,
        achievement__code=achievement_code
    ).update(is_active=active)


def enable_all_achievements_for_students(student_qs):
    AchievementProgress.objects.filter(student__in=student_qs).update(is_active=True)


def disable_all_achievements_for_students(student_qs):
    AchievementProgress.objects.filter(student__in=student_qs).update(is_active=False)


from django.utils.timezone import now
from GameProgress.models.level_schedule import SectionLevelSchedule
from GameProgress.models.level_progress import LevelProgress


def auto_update_lock_states(student_qs):
    current_time = now()
    section_ids = student_qs.values_list("section_id", flat=True).distinct()
    schedules = SectionLevelSchedule.objects.filter(section_id__in=section_ids)

    for sched in schedules:
        # print(
        #     f"[AUTO-UPDATE] Now={current_time} | Start={sched.start_date} | Due={sched.due_date} "
        #     f"| Section={sched.section_id} | Level={sched.level_id}",
        #     flush=True
        # )

        # 🔓 Unlock students in this section if start_date passed
        if sched.start_date and sched.start_date <= current_time:
            updated = LevelProgress.objects.filter(
                student__section_id=sched.section_id,
                level_id=sched.level_id
            ).update(unlocked=True)
            # if updated:
            # print(f"   🔓 Unlocked {updated} rows", flush=True)

        # 🔒 Lock students if due_date passed
        if sched.due_date and sched.due_date <= current_time:
            updated = LevelProgress.objects.filter(
                student__section_id=sched.section_id,
                level_id=sched.level_id
            ).update(unlocked=False)
            # if updated:
            #     print(f"   🔒 Locked {updated} rows", flush=True)

            # 🗑️ Remove the schedule once it's expired
            sched.delete()
            # print(f"   🗑️ Deleted expired schedule (Section={sched.section_id}, Level={sched.level_id})", flush=True)


def unlock_level_with_schedule(student_qs, level_name, section, start_date=None, due_date=None):
    """
    Unlock a specific level for the given students, and optionally apply a due date (and start date)
    via SectionLevelSchedule for that section.
    """
    try:
        level = LevelDefinition.objects.get(name=level_name)
    except LevelDefinition.DoesNotExist:
        return False, f"Level '{level_name}' does not exist."

    with transaction.atomic():
        # 🔓 Unlock for students
        LevelProgress.objects.filter(
            student__in=student_qs,
            level=level
        ).update(unlocked=True)

        # 📅 Create or update schedule entry
        sched, created = SectionLevelSchedule.objects.get_or_create(
            section=section,
            level=level,
            defaults={"start_date": start_date or now(), "due_date": due_date},
        )

        if not created:
            # Update schedule if already exists
            if start_date:
                sched.start_date = start_date
            if due_date:
                sched.due_date = due_date
            sched.save()

    return True, f"Level '{level_name}' unlocked for section {section} with schedule applied."
