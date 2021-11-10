from django.db import models
from django.db.models.fields import CharField
from django.utils.translation import gettext_lazy as _
from i18nfield.fields import I18nCharField
from pretix.base.models import Event, Order
from pretix.base.models.base import LoggedModel
from django_scopes import ScopedManager


class EventPart(LoggedModel):
    class EventPartTypes(models.TextChoices):
        START = "start"
        MIDDLE = "middle"
        END = "end"

    name = CharField(
        max_length=200,
        verbose_name=_("Name"),
    )
    description = I18nCharField(
        max_length=None, verbose_name=_("Description"), default=""
    )
    category = CharField(max_length=200, verbose_name=_("Category"), default="")
    capacity = models.IntegerField(verbose_name=_("Capacity"), default=0)

    type = models.CharField(
        max_length=6,
        verbose_name=_("Type"),
        choices=EventPartTypes.choices,
        default=EventPartTypes.START,
    )
    event = models.ForeignKey(
        Event,
        verbose_name=_("Event"),
        related_name="eventparts",
        on_delete=models.CASCADE,
    )

    orders = models.ManyToManyField(Order)

    objects = ScopedManager(event="event")

    @property
    def type_name(self):
        return self.key_name(self.type)

    def key_name(self, key):
        if key == "start":
            return self.event.settings.eventparts__public_start_name
        if key == "middle":
            return self.event.settings.eventparts__public_middle_name
        if key == "end":
            return self.event.settings.eventparts__public_end_name

    def choices(self):
        x = [(c, self.key_name(c)) for c in self.EventPartTypes.values]
        return x

    def used_places(self) -> int:
        used_places = 0
        for o in self.orders.all().prefetch_related("positions__item"):
            for p in o.positions.all():
                if p.item.admission:
                    used_places += 1
        return used_places

    def contacts(self):
        contacts = []
        for o in self.orders.all():
            contacts.append(o.email)
        return contacts

    def __str__(self):
        return self.name
