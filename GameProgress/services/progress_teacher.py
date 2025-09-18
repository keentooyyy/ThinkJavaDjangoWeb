from django.db import transaction
from django.utils.timezone import now

from GameProgress.models import (
    LevelDefinition,
    AchievementDefinition,
    LevelProgress,
    AchievementProgress
)
from GameProgress.models.level_schedule import SectionLevelSchedule


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
                    AchievementProgress(student_id=student_id, achievement_id=achievement_id, unlocked=False, is_active=True)
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

def auto_update_lock_states(student_qs):
    """Batch update unlock states for all students in queryset based on schedules."""
    current_time = now()

    # Preload schedules per section
    section_ids = student_qs.values_list("section_id", flat=True).distinct()
    schedules = SectionLevelSchedule.objects.filter(section_id__in=section_ids)

    for sched in schedules:
        # Unlock students in this section if start_date passed
        if sched.start_date and sched.start_date <= current_time:
            LevelProgress.objects.filter(
                student__section=sched.section,
                level=sched.level
            ).update(unlocked=True)

        # Lock students in this section if due_date passed
        if sched.due_date and sched.due_date <= current_time:
            LevelProgress.objects.filter(
                student__section=sched.section,
                level=sched.level
            ).update(unlocked=False)
