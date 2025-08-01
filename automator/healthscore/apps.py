from django.apps import AppConfig


class HealthscoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'healthscore'

    def ready(self):
        from . import signals
