from datetime import date
from typing import OrderedDict
from dateutil.relativedelta import relativedelta
from django_scopes import scope
from pretix.base.exporter import ListExporter
from pretix.base.models.items import Item
from pretix.base.models.orders import Order, QuestionAnswer, OrderPosition, Question
from pretix_eventparts.models import EventPart
from enum import Enum
from django import forms
from collections import OrderedDict
from django.utils.translation import gettext, gettext_lazy as _


class ProjectLists(ListExporter):
    identifier = "voco-projectlists"
    verbose_name = "roverVOCO Projektlisten"

    def get_filename(self):
        return "{}_projectlist".format(self.event.slug)

    @property
    def additional_form_fields(self) -> dict:
        return {
            "eventpart": forms.IntegerField(
                label=_("Eventpart ID"),
            ),
        }

    def iterate_list(self, form_data):

        ernaehrung_id = (
            Question.objects.filter(event=self.event).get(identifier="ZN3NGADT").id
        )
        allergie_id = (
            Question.objects.filter(event=self.event).get(identifier="J9TFC7NQ").id
        )
        geburtsdatum_id = (
            Question.objects.filter(event=self.event).get(identifier="EQ3HTNKC").id
        )
        mobil_id = (
            Question.objects.filter(event=self.event).get(identifier="CQEBCKRP").id
        )

        headers = ["Gruppe"]
        headers.append("Name")
        headers.append("Rolle")
        headers.append("E-Mail")
        headers.append("Mobil")
        headers.append("Ernährung")
        headers.append("Allergien")
        headers.append("Geburtsdatum")
        headers.append("Auftakt")

        yield headers

        with scope(event=self.event):

            ep = EventPart.objects.get(id=form_data["eventpart"])

            op: OrderPosition
            for op in ep.get_participant_positions():

                op.cache_answers()

                code = op.order.code
                name = op.attendee_name
                role = op.item.name
                email = op.attendee_email
                mobil = op.answ.get(mobil_id, "")
                ernaehrung = op.answ.get(ernaehrung_id, "")
                allergie = op.answ.get(allergie_id, "")
                geburtsdatum = op.answ.get(geburtsdatum_id, "")

                auftakt = op.order.eventpart_set.get(
                    type=EventPart.EventPartTypes.START
                ).name

                yield [
                    code,
                    name,
                    role,
                    email,
                    mobil,
                    ernaehrung,
                    allergie,
                    geburtsdatum,
                    auftakt,
                ]
