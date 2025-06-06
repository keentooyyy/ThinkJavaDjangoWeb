from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from GameProgress.models import LevelDefinition, LevelProgress, AchievementDefinition, AchievementProgress
from StudentManagementSystem.models.student import Student

import json


@csrf_exempt
def update_game_progress(request, student_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        student = Student.objects.get(id=student_id)
        data = json.loads(request.body)

        for name, values in data.get("levels", {}).get("value", {}).items():
            try:
                level = LevelDefinition.objects.get(name=name)
                progress, _ = LevelProgress.objects.get_or_create(student=student, level=level)
                current = int(values.get("currentTime", 0))
                best = int(values.get("bestTime", 0))
                if current < 0 or best < 0:
                    continue
                if best < progress.best_time:
                    best = progress.best_time
                progress.current_time = current
                progress.best_time = best
                progress.save()
            except:
                continue

        for code, values in data.get("achievements", {}).get("value", {}).items():
            try:
                ach = AchievementDefinition.objects.get(code=code)
                progress, _ = AchievementProgress.objects.get_or_create(student=student, achievement=ach)
                if bool(values.get("unlocked", False)):
                    progress.unlocked = True
                    progress.save()
            except:
                continue

        return JsonResponse({"status": "updated"})
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
