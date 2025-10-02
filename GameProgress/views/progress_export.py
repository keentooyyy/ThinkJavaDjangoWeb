from collections import OrderedDict

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from GameProgress.models import (
    LevelProgress,
    AchievementProgress,
    LevelDefinition,
    AchievementDefinition,
)
from StudentManagementSystem.decorators.custom_decorators import api_login_required
from StudentManagementSystem.models.roles import Role

# Unity-compatible __type strings
LEVEL_TYPE = (
    "System.Collections.Generic.Dictionary`2[[System.String, mscorlib, "
    "Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089],"
    "[LevelData, Assembly-CSharp, Version=0.0.0.0, Culture=neutral, "
    "PublicKeyToken=null]],mscorlib"
)
ACHIEVEMENT_TYPE = (
    "System.Collections.Generic.Dictionary`2[[System.String, mscorlib, "
    "Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089],"
    "[AchievementSaveData, Assembly-CSharp, Version=0.0.0.0, Culture=neutral, "
    "PublicKeyToken=null]],mscorlib"
)


@api_login_required(role=Role.STUDENT, lookup_kwarg="student_id")
@csrf_exempt
def get_game_progress(request, student_id):
    # 🔹 Fetch student (only the ID for efficiency)
    student = request.user_obj

    # 🔹 Bulk-fetch progress
    level_progress = {
        p.level_id: p
        for p in LevelProgress.objects.filter(student=student)
        .only("level_id", "best_time", "current_time", "unlocked")
    }
    achievement_progress = {
        p.achievement_id: p
        for p in AchievementProgress.objects.filter(student=student)
        .only("achievement_id", "unlocked")
    }

    # ------------------------------
    # Levels (ordered by sort_order via model Meta)
    # ------------------------------
    levels = OrderedDict()
    for level in LevelDefinition.objects.only("id", "name", "unlocked", "sort_order"):
        p = level_progress.get(level.id)
        levels[level.name] = {
            "bestTime": p.best_time if p else 0,
            "currentTime": p.current_time if p else 0,
            "unlocked": p.unlocked if p else level.unlocked,
        }

    # ------------------------------
    # Achievements (ordered by code via model Meta)
    # ------------------------------
    achievements = OrderedDict()
    for ach in AchievementDefinition.objects.filter(is_active=True).only("id", "code", "title", "description"):
        p = achievement_progress.get(ach.id)
        achievements[ach.code] = {
            "title": ach.title,
            "description": ach.description,
            "unlocked": p.unlocked if p else False,
        }

    # ------------------------------
    # Response
    # ------------------------------
    return JsonResponse(
        {
            "levels": {
                "__type": LEVEL_TYPE,
                "value": levels,
            },
            "achievements": {
                "__type": ACHIEVEMENT_TYPE,
                "value": achievements,
            },
        },
        json_dumps_params={"indent": 4},
    )
