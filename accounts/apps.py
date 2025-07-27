from django.apps import AppConfig

class AccountsConfig(AppConfig):
    # Specifies the default primary key type for models in this app
    # 'BigAutoField' is recommended for scalability (64-bit integer auto-increment)
    default_auto_field = 'django.db.models.BigAutoField'

    # The dotted path name of the app — used internally by Django
    # This must match the name in INSTALLED_APPS
    name = 'accounts'
