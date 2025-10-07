import logging
import threading
import time
from django.utils.timezone import now
from StudentManagementSystem.models import Student
from GameProgress.models.level_schedule import SectionLevelSchedule
from GameProgress.models.level_progress import LevelProgress

logger = logging.getLogger(__name__)

_background_loop_started = False


def auto_update_lock_states(student_qs):
    """
    Auto-update lock/unlock states for all students based on SectionLevelSchedule.
    - Unlocks a level when its start_date has passed.
    - Locks a level when its due_date has passed, then deletes the schedule.
    - Only updates rows when a change is needed.
    - Safe against teacher overrides since schedules are removed on manual actions.
    """
    current_time = now()
    section_ids = student_qs.values_list("section_id", flat=True).distinct()
    schedules = SectionLevelSchedule.objects.filter(section_id__in=section_ids)

    for sched in schedules:
        try:
            # Unlock students in this section if start_date passed and still locked
            if sched.start_date and sched.start_date <= current_time:
                unlocked_count = LevelProgress.objects.filter(
                    student__section_id=sched.section_id,
                    level_id=sched.level_id,
                    unlocked=False
                ).update(unlocked=True)

                if unlocked_count > 0:
                    logger.info(
                        f"[AUTO-UPDATE] Unlocked {unlocked_count} level(s) "
                        f"(Section={sched.section_id}, Level={sched.level_id})"
                    )

            # Lock students if due_date passed and currently unlocked
            if sched.due_date and sched.due_date <= current_time:
                locked_count = LevelProgress.objects.filter(
                    student__section_id=sched.section_id,
                    level_id=sched.level_id,
                    unlocked=True
                ).update(unlocked=False)

                if locked_count > 0:
                    logger.info(
                        f"[AUTO-UPDATE] Locked {locked_count} level(s) "
                        f"(Section={sched.section_id}, Level={sched.level_id})"
                    )

                # Remove expired schedule once fully processed
                sched.delete()
                logger.info(
                    f"[AUTO-UPDATE] Deleted expired schedule (Section={sched.section_id}, Level={sched.level_id})"
                )

        except Exception as e:
            logger.error(
                f"[AUTO-UPDATE] Error processing schedule (Section={sched.section_id}, Level={sched.level_id}): {e}"
            )


def auto_update_lock_states_cron():
    """
    Run auto lock/unlock update once (manual or scheduled call).
    Safe for cron or background threads.
    """
    try:
        students = Student.objects.all()
        if students.exists():
            auto_update_lock_states(students)
            logger.info(f"[{now()}] Auto update lock/unlock ran for {students.count()} students")
        else:
            logger.info(f"[{now()}] No students found, skipping auto update")
    except Exception as e:
        logger.error(f"[{now()}] Auto update lock/unlock failed: {e}")


def start_auto_update_background():
    """
    Start a background loop that runs auto_update_lock_states_cron() every minute.
    Guaranteed to run only once per Django instance.
    """
    global _background_loop_started
    if _background_loop_started:
        return
    _background_loop_started = True

    def loop():
        while True:
            try:
                auto_update_lock_states_cron()
            except Exception as e:
                logger.error(f"[AUTO-UPDATE LOOP] Error in background loop: {e}")
            time.sleep(60)

    threading.Thread(target=loop, daemon=True).start()
    logger.info("Background auto-update loop started")
