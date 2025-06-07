from GameProgress.models import LevelDefinition, AchievementDefinition
from GameProgress.services.progress import (
    lock_level, unlock_level,
    lock_achievement, unlock_achievement
)


# ---------- DROPDOWNS ----------
def get_level_dropdown():
    return [
        {
            "value": level.name,
            "label": level.name
        }
        for level in LevelDefinition.objects.all()
    ]

def get_achievement_dropdown():
    return [
        {
            "value": ach.code,
            "label": ach.title
        }
        for ach in AchievementDefinition.objects.all()
    ]


# ---------- ACTIONS (use from progress.py) ----------
def lock_level_by_name(level_name):
    return lock_level(level_name)

def unlock_level_by_name(level_name):
    return unlock_level(level_name)

def lock_achievement_by_code(code):
    return lock_achievement(code)

def unlock_achievement_by_code(code):
    return unlock_achievement(code)
