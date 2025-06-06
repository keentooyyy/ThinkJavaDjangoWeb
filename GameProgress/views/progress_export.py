from django.http import JsonResponse
from collections import OrderedDict

from GameProgress.models import LevelProgress, AchievementProgress, LevelDefinition, AchievementDefinition
from StudentManagementSystem.models.student import Student

# Correct ES3-compatible __type strings
LEVEL_TYPE = "System.Collections.Generic.Dictionary`2[[System.String, mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089],[LevelData, Assembly-CSharp, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]],mscorlib"
ACHIEVEMENT_TYPE = "System.Collections.Generic.Dictionary`2[[System.String, mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089],[AchievementSaveData, Assembly-CSharp, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]],mscorlib"

def get_game_progress(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        level_progress = {p.level_id: p for p in LevelProgress.objects.filter(student=student)}
        achievement_progress = {p.achievement_id: p for p in AchievementProgress.objects.filter(student=student)}

        levels = OrderedDict()
        for level in LevelDefinition.objects.all():
            p = level_progress.get(level.id)
            levels[level.name] = {
                "bestTime": p.best_time if p else 0,
                "unlocked": level.unlocked,
                "currentTime": p.current_time if p else 0
            }

        achievements = OrderedDict()
        for ach in AchievementDefinition.objects.all():
            p = achievement_progress.get(ach.id)
            achievements[ach.code] = {
                "title": ach.title,
                "description": ach.description,
                "unlocked": p.unlocked if p else False
            }

        return JsonResponse({
            "levels": {
                "__type": LEVEL_TYPE,
                "value": levels
            },
            "achievements": {
                "__type": ACHIEVEMENT_TYPE,
                "value": achievements
            }
        }, json_dumps_params={"indent": 4})
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)
