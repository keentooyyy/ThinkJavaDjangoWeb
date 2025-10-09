from django.apps import AppConfig


class GameprogressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'GameProgress'

    def ready(self):
        from GameProgress.cron.update_lock_unlock_states import start_auto_update_background
        start_auto_update_background()
