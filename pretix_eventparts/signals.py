# Register your receivers here

from django.contrib.staticfiles import finders
from django.dispatch.dispatcher import receiver

from django.template.loader import render_to_string
from django.urls import resolve, reverse

from django.utils.translation import gettext_lazy as _
from i18nfield.forms import LazyI18nString

from pretix.base.settings import settings_hierarkey
from pretix.base.signals import layout_text_variables, logentry_display
from pretix.control import signals
from pretix.presale.signals import (
    order_info,
    sass_postamble,
)


from pretix_eventparts.models import EventPart

settings_hierarkey.add_default(
    key="eventparts__public_name", default_type=LazyI18nString, value=None
)
settings_hierarkey.add_default(
    key="eventparts__public_description", default_type=LazyI18nString, value=None
)
settings_hierarkey.add_default(
    key="eventparts__public_start_name", default_type=LazyI18nString, value=None
)
settings_hierarkey.add_default(
    key="eventparts__public_middle_name", default_type=LazyI18nString, value=None
)
settings_hierarkey.add_default(
    key="eventparts__public_end_name", default_type=LazyI18nString, value=None
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
def order_eventstep_selection(sender, order, request, **kwargs):
    ep = order.eventpart_set.all()

    eventparts = {
        "start": ep.filter(type=EventPart.EventPartTypes.START).first(),
        "middle": ep.filter(type=EventPart.EventPartTypes.MIDDLE).first(),
        "end": ep.filter(type=EventPart.EventPartTypes.END).first(),
    }

    return render_to_string(
        "pretix_eventparts/eventparts/eventpart_assignments.html",
        {"order": order, "eventparts": eventparts, "request": request},
    )


@receiver(order_info, dispatch_uid="pretix_eventparts")
def order_eventstep_selection_public(sender, order, request, **kwargs):
    if request.event.settings.eventparts__public is False:
        return None

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
            "Eventstep information is switched to public and is shown in the customers order view."
        )
    if logentry.action_type == "pretix_eventparts.not_public":
        return _(
            "Eventstep information is no longer shown in the customers order view."
        )
    return None


@receiver(layout_text_variables, dispatch_uid="pretix_eventparts")
def ticket_text_variables(**kwargs):
    return {
        "pretix_eventsteps_start_type": {
            "label": _("1st Eventstep Type"),
            "editor_sample": _("1st Step Type"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .type_name,
        },
        "pretix_eventsteps_start_name": {
            "label": _("1st Eventstep Name"),
            "editor_sample": _("1st Step Name"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .name,
        },
        "pretix_eventsteps_start_description": {
            "label": _("1st Eventstep Description"),
            "editor_sample": _("Descriptive Text ..."),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .description,
        },
        "pretix_eventsteps_start_category": {
            "label": _("1st Eventstep Category"),
            "editor_sample": _("Category 1"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.START
            )
            .first()
            .category,
        },
        "pretix_eventsteps_middle_type": {
            "label": _("2nd Eventstep Type"),
            "editor_sample": _("2nd Step Type"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .type_name,
        },
        "pretix_eventsteps_middle_name": {
            "label": _("2nd Eventstep Name"),
            "editor_sample": _("2nd Step Name"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .name,
        },
        "pretix_eventsteps_middle_description": {
            "label": _("2nd Eventstep Description"),
            "editor_sample": _("Descriptive Text ..."),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .description,
        },
        "pretix_eventsteps_middle_category": {
            "label": _("2nd Eventstep Category"),
            "editor_sample": _("Category 2"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.MIDDLE
            )
            .first()
            .category,
        },
        "pretix_eventsteps_end_type": {
            "label": _("3rd Eventstep Type"),
            "editor_sample": _("3rd Step Type"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .type_name,
        },
        "pretix_eventsteps_end_name": {
            "label": _("3rd Eventstep Name"),
            "editor_sample": _("3rd Step Name"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .name,
        },
        "pretix_eventsteps_end_description": {
            "label": _("3rd Eventstep Description"),
            "editor_sample": _("Descriptive Text ..."),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .description,
        },
        "pretix_eventsteps_end_category": {
            "label": _("3rd Eventstep Category"),
            "editor_sample": _("Category 3"),
            "evaluate": lambda orderposition, order, event: order.eventpart_set.filter(
                type=EventPart.EventPartTypes.END
            )
            .first()
            .category,
        },
    }
