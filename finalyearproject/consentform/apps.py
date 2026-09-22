from django.apps import AppConfig


class ConsentformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consentform'

def ready(self):
    import consentform.signals