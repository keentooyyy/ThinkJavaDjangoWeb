# GameProgress/cron.py
import logging, threading, time
from django.utils.timezone import now
from StudentManagementSystem.models import Student
from GameProgress.services.progress_teacher import auto_update_lock_states

# Global flag
_background_loop_started = False

def auto_update_lock_states_cron():
    """
    Run auto lock/unlock update once (manual call).
    Safe for use in cron-like schedulers (django-crontab, Task Scheduler).
    """
    try:
        students = Student.objects.all()
        auto_update_lock_states(students)
        logging.getLogger(__name__).info(f"Auto update lock/unlock ran at {now()}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Auto update lock/unlock failed: {e}")


def start_auto_update_background():
    """
    Start a background loop that runs auto_update_lock_states_cron() every minute.
    Guaranteed to run only once.
    """
    global _background_loop_started
    if _background_loop_started:  # already running → do nothing
        return
    _background_loop_started = True

    def loop():
        while True:
            auto_update_lock_states_cron()
            time.sleep(60)  # wait 1 min

    threading.Thread(target=loop, daemon=True).start()
    logging.getLogger(__name__).info("Background auto-update loop started")
