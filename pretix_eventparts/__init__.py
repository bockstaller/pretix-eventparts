from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.0.0"


class PluginApp(PluginConfig):
    name = "pretix_eventparts"
    verbose_name = "pretix eventparts"

    class PretixPluginMeta:
        name = gettext_lazy("pretix eventparts")
        author = "Lukas Bockstaller"
        description = gettext_lazy("Short description")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=4.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = "pretix_eventparts.PluginApp"
