from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"
    verbose_name = "Common"

    def ready(self):
        from common.django_compat import patch_django_context_copy_for_python_314

        patch_django_context_copy_for_python_314()
