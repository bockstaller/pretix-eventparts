from django.db import models
from django.db.models.fields import CharField
from django.utils.translation import gettext_lazy as _

from i18nfield.fields import I18nCharField
import logging


from pretix.base.models import Event, Order, OrderPosition, Question
from pretix.base.models.base import LoggedModel

logger = logging.getLogger(__name__)


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

    # objects = ScopedManager(event="event")

    def get_contact_info(self):

        phone = []
        names = []
        emails = []
        participants = []

        def contact(o: Order):
            leader_product_id = 27
            try:
                leader = o.positions.get(item__id=leader_product_id)
            except OrderPosition.DoesNotExist:
                return ("", "")
            leader.cache_answers()
            return (
                leader.attendee_name,
                leader.attendee_email,
                leader.answ.get(mobil_id, ""),
            )

        try:
            mobil_id = (
                Question.objects.filter(event=self.event).get(identifier="CQEBCKRP").id
            )

            o: Order
            for o in self.orders.exclude(status=Order.STATUS_CANCELED).all():
                name, email, phone_no = contact(o)
                names.append(name)
                emails.append(email)
                phone.append(phone_no)

                participants.append(
                    len(self.get_participant_positions().filter(order=o))
                )
        except Exception as e:
            logger.error(e)
        finally:
            return {
                "phone": phone,
                "names": names,
                "emails": emails,
                "participants": participants,
            }

    def get_participant_positions(self):

        return (
            OrderPosition.objects.filter(item__admission=True)
            .filter(order__in=self.orders.all())
            .filter(canceled=False)
            .exclude(item__id__in=[51, 45, 53])
            .order_by("-order__code")
        )

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

        used_places = len(self.get_participant_positions())

        return used_places

    def contacts(self):
        contacts = []
        for o in self.orders.all():
            contacts.append(o.email)
        return contacts

    def __str__(self):
        return self.name
