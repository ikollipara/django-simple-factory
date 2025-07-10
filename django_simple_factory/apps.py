from importlib import import_module

from django.apps import AppConfig


class DjangoFactoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_simple_factory"

    def ready(self) -> None:
        from django.apps import apps

        from . import factories

        for config in apps.get_app_configs():
            try:
                if config.name != self.name:
                    module = import_module(f"{config.name}.factories")
                    for item in module.__dict__.values():
                        if isinstance(item, type) and issubclass(
                            item, factories.Factory
                        ):
                            factories.Factory._registry[
                                f"{config.name.split('.')[-1]}.{item.__name__}"
                            ] = item
            except (ImportError, ModuleNotFoundError):
                pass
