# Register your receivers here

from django.contrib.staticfiles import finders
from django.dispatch.dispatcher import receiver
from django.template.loader import render_to_string
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from django_scopes import scope
from i18nfield.forms import LazyI18nString
from pretix.base.settings import settings_hierarkey
from pretix.base.signals import (
    layout_text_variables,
    logentry_display,
    register_data_exporters,
)
from pretix.control import signals
from pretix.presale.signals import order_info, sass_postamble
from pretix.base.email import (
    SimpleFunctionalMailTextPlaceholder,
    register_mail_placeholders,
)
from pretix_eventparts.exporter import ProjectLists
from pretix_eventparts.models import EventPart
from django.core.exceptions import ObjectDoesNotExist


@receiver(register_data_exporters, dispatch_uid="voco-projectlists")
def register_post_exporter(sender, **kwargs):

    return ProjectLists


settings_hierarkey.add_default(
    key="eventparts__public_name", default_type=LazyI18nString, value="Eventpart"
)
settings_hierarkey.add_default(
    key="eventparts__public_description", default_type=LazyI18nString, value=None
)
settings_hierarkey.add_default(
    key="eventparts__public_start_name", default_type=LazyI18nString, value="Start"
)
settings_hierarkey.add_default(
    key="eventparts__public_middle_name", default_type=LazyI18nString, value="Middle"
)
settings_hierarkey.add_default(
    key="eventparts__public_end_name", default_type=LazyI18nString, value="End"
)


@receiver(signals.nav_event, dispatch_uid="pretix_eventparts")
def navbar_entry(request, **kwargs):
    url = resolve(request.path_info)
    nav = [
        {
            "label": _("Eventparts"),
            "url": reverse(
                "plugins:pretix_eventparts:eventpart.list",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.url_name == "eventpart.list",
            "icon": "forward",
        }
    ]
    return nav


@receiver(signals.order_info, dispatch_uid="pretix_eventparts")
def order_eventpart_selection(sender, order, request, **kwargs):
    with scope(event=order.event):
        ep = order.eventpart_set.all()
        eventparts = {
            "start": ep.filter(type=EventPart.EventPartTypes.START).first(),
            "middle": ep.filter(type=EventPart.EventPartTypes.MIDDLE).first(),
            "end": ep.filter(type=EventPart.EventPartTypes.END).first(),
        }

    return render_to_string(
        "pretix_eventparts/eventparts/eventpart_assignments.html",
        {
            "order": order,
            "eventparts": eventparts,
            "request": request,
            "settings": request.event.settings,
        },
    )


@receiver(order_info, dispatch_uid="pretix_eventparts")
def order_eventpart_selection_public(sender, order, request, **kwargs):
    if request.event.settings.eventparts__public is False:
        return None

    with scope(event=order.event):
        ep = order.eventpart_set.all()
        eventparts = {
            "start": ep.filter(type=EventPart.EventPartTypes.START).first(),
            "middle": ep.filter(type=EventPart.EventPartTypes.MIDDLE).first(),
            "end": ep.filter(type=EventPart.EventPartTypes.END).first(),
        }

    return render_to_string(
        "pretix_eventparts/eventparts/eventpart_assignments_public.html",
        {
            "order": order,
            "eventparts": eventparts,
            "request": request,
            "settings": request.event.settings,
        },
    )


@receiver(sass_postamble, dispatch_uid="pretix_eventparts")
def r_sass_postamble(filename, **kwargs):
    if filename == "main.scss":
        with open(finders.find("pretix_eventparts/postamble.scss"), "r") as fp:
            return fp.read()
    return " "


@receiver(signals.nav_event_settings, dispatch_uid="pretix_eventparts")
def nav_event_settings(sender, request, **kwargs):
    url = resolve(request.path_info)
    if not request.user.has_event_permission(
        request.organizer, request.event, "can_change_event_settings", request=request
    ):
        return []
    return [
        {
            "label": _("Eventparts"),
            "url": reverse(
                "plugins:pretix_eventparts:eventpart.settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.organizer.slug,
                },
            ),
            "active": url.url_name == "eventpart.settings",
        }
    ]


@receiver(logentry_display, dispatch_uid="pretix_eventparts")
def logentry_display_f(logentry, **kwargs):
    if logentry.action_type == "pretix_eventparts.public":
        return _(
            "Eventpart information is switched to public and is shown in the customers order view."
        )
    if logentry.action_type == "pretix_eventparts.not_public":
        return _(
            "Eventpart information is no longer shown in the customers order view."
        )
    return None


def format_as_table(ep):
    if ep is None:
        return ""

    contact_info = ep.get_contact_info()
    start = "<table>"
    header = "<tr> <th>Name</th> <th>Email</th> <th>Telefonnummer</th> <th>Gruppengröße</th> </tr>"

    rows = [
        f"<tr> <td>  {n}&nbsp;&nbsp;</td> <td>  {e}&nbsp;&nbsp;</td> <td>  {p}&nbsp;&nbsp;</td> <td>  {pa}&nbsp;&nbsp;</td> </tr>"
        for n, e, p, pa in zip(
            contact_info.get("names"),
            contact_info.get("emails"),
            contact_info.get("phone"),
            contact_info.get("participants"),
        )
    ]
    end = "</table>"
    return "".join(
        [
            start,
            header,
        ]
        + rows
        + [end]
    )


@receiver(layout_text_variables, dispatch_uid="pretix_eventparts")
def ticket_text_variables(**kwargs):
    return {
        "pretix_eventparts_start_type": {
            "label": _("1st Eventpart Type"),
            "editor_sample": _("1st Part Type"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .type_name,
        },
        "pretix_eventparts_start_name": {
            "label": _("1st Eventpart Name"),
            "editor_sample": _("1st Part Name"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .name,
        },
        "pretix_eventparts_start_description": {
            "label": _("1st Eventpart Description"),
            "editor_sample": _("Descriptive Text ..."),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .description,
        },
        "pretix_eventparts_start_category": {
            "label": _("1st Eventpart Category"),
            "editor_sample": _("Category 1"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .category,
        },
        "pretix_eventparts_middle_type": {
            "label": _("2nd Eventpart Type"),
            "editor_sample": _("2nd Part Type"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .type_name,
        },
        "pretix_eventparts_middle_name": {
            "label": _("2nd Eventpart Name"),
            "editor_sample": _("2nd Part Name"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .name,
        },
        "pretix_eventparts_middle_description": {
            "label": _("2nd Eventpart Description"),
            "editor_sample": _("Descriptive Text ..."),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .description,
        },
        "pretix_eventparts_middle_category": {
            "label": _("2nd Eventpart Category"),
            "editor_sample": _("Category 2"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .category,
        },
        "pretix_eventparts_end_type": {
            "label": _("3rd Eventpart Type"),
            "editor_sample": _("3rd Part Type"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .type_name,
        },
        "pretix_eventparts_end_name": {
            "label": _("3rd Eventpart Name"),
            "editor_sample": _("3rd Part Name"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .name,
        },
        "pretix_eventparts_end_description": {
            "label": _("3rd Eventpart Description"),
            "editor_sample": _("Descriptive Text ..."),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .description,
        },
        "pretix_eventparts_end_category": {
            "label": _("3rd Eventpart Category"),
            "editor_sample": _("Category 3"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .category,
        },
    }


def returns_string(model, attribute):
    try:
        return getattr(model, attribute)
    except AttributeError:
        return ""


FirstPartType = SimpleFunctionalMailTextPlaceholder(
    "1st_part_type",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.START).first(),
        "type_name",
    ),
    sample="1st Eventpart Type",
)

FirstPartName = SimpleFunctionalMailTextPlaceholder(
    "1st_part_name",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.START).first(), "name"
    ),
    sample="1st Eventpart Name",
)

FirstPartDescription = SimpleFunctionalMailTextPlaceholder(
    "1st_part_description",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.START).first(),
        "description",
    ),
    sample="1st Eventpart Description",
)

FirstPartCategory = SimpleFunctionalMailTextPlaceholder(
    "1st_part_category",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.START).first(),
        "category",
    ),
    sample="1st Eventpart Category",
)

SecondPartType = SimpleFunctionalMailTextPlaceholder(
    "2nd_part_type",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.MIDDLE).first(),
        "type_name",
    ),
    sample="2nd Eventpart Type",
)

SecondPartName = SimpleFunctionalMailTextPlaceholder(
    "2nd_part_name",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.MIDDLE).first(), "name"
    ),
    sample="2nd Eventpart Name",
)

SecondPartDescription = SimpleFunctionalMailTextPlaceholder(
    "2nd_part_description",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.MIDDLE).first(),
        "description",
    ),
    sample="2nd Eventpart Description",
)

SecondPartCategory = SimpleFunctionalMailTextPlaceholder(
    "2nd_part_category",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.MIDDLE).first(),
        "category",
    ),
    sample="2nd Eventpart Category",
)

SecondPartParticipants = SimpleFunctionalMailTextPlaceholder(
    "2nd_part_participants",
    ["order"],
    lambda order: format_as_table(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.MIDDLE).first()
    ),
    sample=""" <table>
  <tr>
    <th>Name</th>
    <th>Email</th>
    <th>Telefonnummer</th>
    <th>Gruppengröße</th>
  </tr>
  <tr>
    <td>Peter</td>
    <td>peter@testd.de</td>
    <td>017....</td>
    <td>32</td>
  </tr>
  
</table>  """,
)

ThirdPartType = SimpleFunctionalMailTextPlaceholder(
    "3rd_part_type",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.END).first(),
        "type_name",
    ),
    sample="3rd Eventpart Type",
)

ThirdPartName = SimpleFunctionalMailTextPlaceholder(
    "3rd_part_name",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.END).first(),
        "name",
    ),
    sample="3rd Eventpart Name",
)

ThirdPartDescription = SimpleFunctionalMailTextPlaceholder(
    "3rd_part_description",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.END).first(),
        "description",
    ),
    sample="3rd Eventpart Description",
)

ThirdPartCategory = SimpleFunctionalMailTextPlaceholder(
    "3rd_part_category",
    ["order"],
    lambda order: returns_string(
        order.eventpart_set.filter(type=EventPart.EventPartTypes.END).first(),
        "category",
    ),
    sample="3rd Eventpart Category",
)

mail_placeholders = [
    FirstPartType,
    FirstPartName,
    FirstPartDescription,
    FirstPartCategory,
    SecondPartType,
    SecondPartName,
    SecondPartDescription,
    SecondPartCategory,
    SecondPartParticipants,
    ThirdPartType,
    ThirdPartName,
    ThirdPartDescription,
    ThirdPartCategory,
]


@receiver(register_mail_placeholders, dispatch_uid="eventparts_placeholders")
def register_mail_renderers(sender, **kwargs):

    return mail_placeholders
