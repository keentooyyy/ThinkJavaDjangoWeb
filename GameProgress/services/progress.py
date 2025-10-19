from django.db import transaction
from django.shortcuts import get_object_or_404

from GameProgress.models import (
    LevelDefinition,
    AchievementDefinition,
    LevelProgress,
    AchievementProgress,
)
from GameProgress.models.level_schedule import SectionLevelSchedule
from StudentManagementSystem.models.student import Student


# ============================================================
# 🔹 GLOBAL SYNCHRONIZATION
# ============================================================

def sync_all_students_with_all_progress():
    """
    Ensure every student has progress rows for all Level and Achievement definitions.
    Creates any missing LevelProgress / AchievementProgress records.
    """
    students = list(Student.objects.values_list("id", flat=True))
    levels = list(LevelDefinition.objects.values_list("id", flat=True))
    achievements = list(AchievementDefinition.objects.values_list("id", flat=True))

    existing_levels = set(LevelProgress.objects.values_list("student_id", "level_id"))
    existing_achievements = set(AchievementProgress.objects.values_list("student_id", "achievement_id"))

    new_level_progress = []
    new_achievement_progress = []

    for student_id in students:
        for level_id in levels:
            if (student_id, level_id) not in existing_levels:
                new_level_progress.append(
                    LevelProgress(student_id=student_id, level_id=level_id)
                )

        for achievement_id in achievements:
            if (student_id, achievement_id) not in existing_achievements:
                new_achievement_progress.append(
                    AchievementProgress(student_id=student_id, achievement_id=achievement_id)
                )

    with transaction.atomic():
        if new_level_progress:
            LevelProgress.objects.bulk_create(new_level_progress, batch_size=1000, ignore_conflicts=True)
        if new_achievement_progress:
            AchievementProgress.objects.bulk_create(new_achievement_progress, batch_size=1000, ignore_conflicts=True)

    print(f"✅ Sync completed! ({len(new_level_progress)} new LevelProgress, {len(new_achievement_progress)} new AchievementProgress)")


# ============================================================
# 🔹 LEVEL DEFINITIONS (GLOBAL)
# ============================================================

def add_level(name: str, unlocked: bool = False):
    """
    Create or retrieve a LevelDefinition globally.
    """
    level, _ = LevelDefinition.objects.get_or_create(name=name, defaults={"unlocked": unlocked})
    return level


def lock_level(level_name: str):
    """
    Globally lock a single level.
    """
    level = get_object_or_404(LevelDefinition, name=level_name)
    level.unlocked = False
    level.save(update_fields=["unlocked"])
    return level


def unlock_level(level_name: str):
    """
    Globally unlock a single level.
    """
    level = get_object_or_404(LevelDefinition, name=level_name)
    level.unlocked = True
    level.save(update_fields=["unlocked"])
    return level


def lock_all_levels():
    """Globally lock ALL levels."""
    LevelDefinition.objects.update(unlocked=False)
    print("🔒 All levels globally locked.")


def unlock_all_levels():
    """Globally unlock ALL levels."""
    LevelDefinition.objects.update(unlocked=True)
    print("🔓 All levels globally unlocked.")


# ============================================================
# 🔹 ACHIEVEMENT DEFINITIONS (GLOBAL)
# ============================================================

def add_achievement(code: str, title: str, description: str):
    """
    Create or retrieve an AchievementDefinition globally.
    """
    ach, _ = AchievementDefinition.objects.get_or_create(
        code=code,
        defaults={"title": title, "description": description, "is_active": True},
    )
    return ach


def set_achievement_active(code: str, active: bool = True):
    """
    Globally set whether an AchievementDefinition is active (unlockable).
    """
    ach = get_object_or_404(AchievementDefinition, code=code)
    ach.is_active = active
    ach.save(update_fields=["is_active"])
    return ach


def enable_all_achievements():
    """Globally mark all achievements as active."""
    AchievementDefinition.objects.update(is_active=True)
    print("🏆 All achievements globally enabled.")


def disable_all_achievements():
    """Globally disable all achievements."""
    AchievementDefinition.objects.update(is_active=False)
    print("🚫 All achievements globally disabled.")


# ============================================================
# 🔹 GLOBAL BULK HELPERS
# ============================================================

def reset_all_progress():
    """
    Completely reset all levels and achievements globally and per student.

    ✅ Source of Truth Reset:
    - Locks all LevelDefinition entries globally.
    - Resets all per-student LevelProgress and AchievementProgress.
    - Deletes all SectionLevelSchedule entries (so cron can't re-unlock old levels).
    - Ensures all teacher and cron schedules are wiped clean.
    """
    sync_all_students_with_all_progress()
    with transaction.atomic():
        # 1️⃣ Lock all global levels
        LevelDefinition.objects.update(unlocked=False)

        # 2️⃣ Reset per-student progress
        LevelProgress.objects.update(best_time=0, current_time=0, unlocked=False)
        AchievementProgress.objects.update(unlocked=False, is_active=True)

        # 3️⃣ 🚨 Remove all active schedules so no background cron can alter state afterward
        deleted_count, _ = SectionLevelSchedule.objects.all().delete()

    print(
        f"✅ Global reset complete:\n"
        f"   - All levels locked\n"
        f"   - All progress reset\n"
        f"   - Cleared {deleted_count} schedule(s) to prevent re-unlocking"
    )
