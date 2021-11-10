from django.contrib import messages
from django.db import transaction
from django.http import (
    Http404,
    HttpResponseRedirect,
)
from django.urls import resolve, reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView
from django.views.generic.edit import DeleteView
from pretix.base.models import Event, Order
from pretix.control.permissions import EventPermissionRequiredMixin
from pretix.control.views import (
    CreateView,
    PaginationMixin,
    UpdateView,
)
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin
from pretix.helpers.models import modelcopy
from pretix.presale.style import regenerate_css

from pretix_eventparts.forms import (
    AssignEventPartForm,
    EventPartForm,
    EventpartSettingsForm,
)
from pretix_eventparts.models import EventPart
from django_scopes import scope


class EventPartCreate(EventPermissionRequiredMixin, CreateView):
    model = EventPart
    form_class = EventPartForm
    template_name = "pretix_eventparts/eventparts/eventpart.html"
    permission = "can_change_items"
    context_object_name = "eventpart"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_eventparts:eventpart.list",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    @cached_property
    def copy_from(self):
        if self.request.GET.get("copy_from") and not getattr(self, "object", None):
            try:
                return self.request.event.eventparts.get(
                    pk=self.request.GET.get("copy_from")
                )
            except EventPart.DoesNotExist:
                pass

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.copy_from:
            i = modelcopy(self.copy_from)
            i.pk = None
            kwargs["instance"] = i
        else:
            kwargs["instance"] = EventPart(event=self.request.event)
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        form.instance.event = self.request.event
        messages.success(self.request, _("The new Eventpart has been created."))
        ret = super().form_valid(form)
        form.instance.log_action(
            "pretix_eventparts.eventpart.added",
            data=dict(form.cleaned_data),
            user=self.request.user,
        )
        return ret

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)


class EventPartDelete(EventPermissionRequiredMixin, DeleteView):
    model = EventPart
    form_class = EventPartForm
    template_name = "pretix_eventparts/eventparts/eventpart_delete.html"
    permission = "can_change_items"
    context_object_name = "eventpart"

    def get_object(self, queryset=None) -> EventPart:
        with scope(event=self.request.event):
            try:
                return self.request.event.eventparts.get(id=self.kwargs["eventpart"])
            except EventPart.DoesNotExist:
                raise Http404(_("The requested product category does not exist."))

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        with scope(event=self.request.event):
            self.object = self.get_object()

            success_url = self.get_success_url()
            self.object.log_action(
                "pretix_eventparts.eventpart.deleted", user=self.request.user
            )
            self.object.delete()
            messages.success(request, _("The selected eventpart has been deleted."))
            return HttpResponseRedirect(success_url)

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_eventparts:eventpart.list",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )


class EventPartUpdate(EventPermissionRequiredMixin, UpdateView):
    model = EventPart
    form_class = EventPartForm
    template_name = "pretix_eventparts/eventparts/eventpart.html"
    permission = "can_change_items"
    context_object_name = "eventpart"

    def get_object(self, queryset=None) -> EventPart:
        with scope(event=self.request.event):
            url = resolve(self.request.path_info)
            try:
                x = self.request.event.eventparts.get(id=url.kwargs["eventpart"])
                return x
            except EventPart.DoesNotExist:
                raise Http404(_("The requested eventpart does not exist."))

    @transaction.atomic
    def form_valid(self, form):
        with scope(event=self.request.event):
            messages.success(self.request, _("Your changes have been saved."))
            if form.has_changed():
                self.object.log_action(
                    "pretix_eventparts.eventpart.changed",
                    user=self.request.user,
                    data={k: form.cleaned_data.get(k) for k in form.changed_data},
                )
            return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_eventparts:eventpart.list",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)


class EventPartList(EventPermissionRequiredMixin, PaginationMixin, ListView):
    model = EventPart
    context_object_name = "eventparts"
    template_name = "pretix_eventparts/eventparts/eventparts.html"
    permission = "can_view_orders"

    def get_queryset(self):
        with scope(event=self.request.event):
            qs = EventPart.objects.filter(event=self.request.event)

            return qs

    def get_context_data(self, **kwargs):
        with scope(event=self.request.event):
            ctx = super().get_context_data(**kwargs)
            ctx["start"] = self.request.event.settings.eventparts__public_start_name
            ctx["middle"] = self.request.event.settings.eventparts__public_middle_name
            ctx["end"] = self.request.event.settings.eventparts__public_end_name
            return ctx


class EventPartAssign(EventPermissionRequiredMixin, FormView):
    form_class = AssignEventPartForm
    template_name = "pretix_eventparts/eventparts/eventpart_assign.html"
    permission = "can_change_items"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.request.event
        return kwargs

    def get_initial(self):
        with scope(event=self.request.event):
            url = resolve(self.request.path_info)
            order = Order.objects.filter(code=url.kwargs["code"]).get()

            initial = {
                "eventpart_start": order.eventpart_set.filter(
                    type=EventPart.EventPartTypes.START
                ).first(),
                "eventpart_middle": order.eventpart_set.filter(
                    type=EventPart.EventPartTypes.MIDDLE
                ).first(),
                "eventpart_end": order.eventpart_set.filter(
                    type=EventPart.EventPartTypes.END
                ).first(),
            }
            return initial

    @transaction.atomic
    def form_valid(self, form):
        with scope(event=self.request.event):
            url = resolve(self.request.path_info)
            order = Order.objects.get(code=url.kwargs["code"])
            order.eventpart_set.clear()
            order.eventpart_set.add(
                form.cleaned_data["eventpart_start"],
                form.cleaned_data["eventpart_middle"],
                form.cleaned_data["eventpart_end"],
            )
            return super().form_valid(form)

    def get_success_url(self) -> str:
        with scope(event=self.request.event):
            url = resolve(self.request.path_info)
            return reverse(
                "control:event.order",
                kwargs={
                    "organizer": self.request.event.organizer.slug,
                    "event": self.request.event.slug,
                    "code": url.kwargs["code"],
                },
            )

    def form_invalid(self, form):
        with scope(event=self.request.event):
            messages.error(
                self.request,
                _("We could not save your changes. See below for details."),
            )
            return super().form_invalid(form)


class SettingsView(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = EventpartSettingsForm
    template_name = "pretix_eventparts/eventparts/settings.html"
    permission = "can_change_settings"

    def form_success(self):
        form = self.get_form()
        if form.is_valid():

            if form.cleaned_data["eventparts__public"] is True:
                regenerate_css.apply_async(args=(self.request.event.pk,))
                self.request.event.log_action(
                    "pretix_eventparts.public", user=self.request.user
                )
            else:
                self.request.event.log_action(
                    "pretix_eventparts.not_public", user=self.request.user
                )
        return super().form_success()

    def get_success_url(self):
        return reverse(
            "plugins:pretix_eventparts:eventpart.settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )
