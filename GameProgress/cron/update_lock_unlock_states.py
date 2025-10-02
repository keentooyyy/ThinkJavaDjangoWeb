# GameProgress/cron.py
import logging, threading, time
from django.utils.timezone import now
from StudentManagementSystem.models import Student
from GameProgress.services.progress_teacher import auto_update_lock_states

# Global flag
_background_loop_started = False

logger = logging.getLogger(__name__)

def auto_update_lock_states_cron():
    """
    Run auto lock/unlock update once (manual call).
    Safe for use in cron-like schedulers (django-crontab, Task Scheduler).
    """
    try:
        students = Student.objects.all()
        auto_update_lock_states(students)
        # msg = f"[{now()}] ✅ Auto update lock/unlock ran for {students.count()} students"
        # logger.info(msg)
        # print(msg, flush=True)   # 🔹 print only useful success log
    except Exception as e:
        msg = f"[{now()}] ❌ Auto update lock/unlock failed: {e}"
        logger.error(msg)
        print(msg, flush=True)   # 🔹 print only error log


def start_auto_update_background():
    """
    Start a background loop that runs auto_update_lock_states_cron() every minute.
    Guaranteed to run only once.
    """
    global _background_loop_started
    if _background_loop_started:
        return
    _background_loop_started = True

    def loop():
        while True:
            auto_update_lock_states_cron()
            time.sleep(60)  # no noisy heartbeat

    threading.Thread(target=loop, daemon=True).start()
    logger.info("Background auto-update loop started")
    # no extra print here
