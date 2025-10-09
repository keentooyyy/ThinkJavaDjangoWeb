import logging
import threading

from GameProgress.services.progress import sync_all_students_with_all_progress


def run_sync_in_background():
    """
    Fire sync_all_students_with_all_progress() in a background thread.
    Can be used in views or anywhere else.
    """

    def task():
        try:
            sync_all_students_with_all_progress()
        except Exception as e:
            logging.getLogger(__name__).error("Background sync failed: %s", str(e))

    threading.Thread(target=task, daemon=True).start()
