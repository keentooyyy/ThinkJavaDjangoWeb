import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from GameProgress.models import (
    LevelDefinition,
    LevelProgress,
    AchievementDefinition,
    AchievementProgress,
)
from StudentManagementSystem.decorators.custom_decorators import api_login_required
from StudentManagementSystem.models.roles import Role


@csrf_exempt
@api_login_required(role=Role.STUDENT, lookup_kwarg="student_id")
def update_game_progress(request, student_id):
    """
    Updates a student's existing level and achievement progress.
    - Ownership & role enforced by api_login_required.
    - Does not create new progress records.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        student = request.user_obj  # ✅ injected by decorator
        data = json.loads(request.body)

        # Prefetch existing progress
        existing_levels = {
            lp.level_id: lp
            for lp in LevelProgress.objects.filter(student=student)
        }
        existing_achs = {
            ap.achievement_id: ap
            for ap in AchievementProgress.objects.filter(student=student)
        }

        # Bulk fetch definitions (ordered by Meta)
        level_defs = {lvl.name: lvl for lvl in LevelDefinition.objects.all()}
        achievement_defs = {
            ach.code: ach
            for ach in AchievementDefinition.objects.filter(is_active=True)
        }

        update_level_objs, update_ach_objs = [], []

        # ------------------------------
        # Levels
        # ------------------------------
        for name, values in data.get("levels", {}).get("value", {}).items():
            level = level_defs.get(name)
            if not level:
                continue

            progress = existing_levels.get(level.id)
            if not progress:
                continue  # skip if no existing record

            current = int(values.get("currentTime", 0))
            best = int(values.get("bestTime", 0))

            if current < 0 or best < 0:
                continue

            if best < progress.best_time:
                best = progress.best_time

            progress.current_time = current
            progress.best_time = best
            progress.unlocked = values.get("unlocked", progress.unlocked)
            update_level_objs.append(progress)

        # ------------------------------
        # Achievements
        # ------------------------------
        for code, values in data.get("achievements", {}).get("value", {}).items():
            ach = achievement_defs.get(code)
            if not ach:
                continue

            progress = existing_achs.get(ach.id)
            if not progress:
                continue  # skip if no existing record

            unlocked = bool(values.get("unlocked", False))
            if unlocked and not progress.unlocked:
                progress.unlocked = True
                update_ach_objs.append(progress)

        # ------------------------------
        # Batch update inside a transaction
        # ------------------------------
        with transaction.atomic():
            if update_level_objs:
                LevelProgress.objects.bulk_update(
                    update_level_objs, ["current_time", "best_time", "unlocked"]
                )
            if update_ach_objs:
                AchievementProgress.objects.bulk_update(update_ach_objs, ["unlocked"])

        return JsonResponse({"status": "updated"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
