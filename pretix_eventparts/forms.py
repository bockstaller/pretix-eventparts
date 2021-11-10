from django import forms
from django.utils.translation import gettext_lazy as _
from i18nfield.forms import I18nFormField, I18nTextarea, I18nTextInput, LazyI18nString
from pretix.base.forms import I18nModelForm, SettingsForm

from pretix_eventparts.models import EventPart
from django_scopes.forms import SafeModelChoiceField
from django_scopes import scope


class EventPartForm(I18nModelForm):
    class Meta:
        model = EventPart
        localized_fields = "__all__"
        fields = ["name", "description", "category", "type", "capacity"]
        widgets = {"description": I18nTextarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = self.instance.choices


class AssignEventPartForm(forms.Form):
    class Meta:
        field_classes = {
            "eventpart_start": SafeModelChoiceField,
            "eventpart_middle": SafeModelChoiceField,
            "eventpart_end": SafeModelChoiceField,
        }

    def __init__(self, event, **kwargs):
        super().__init__(**kwargs)
        with scope(event=event):
            self.fields["eventpart_start"].queryset = EventPart.objects.filter(
                type=EventPart.EventPartTypes.START
            ).all()
            self.fields["eventpart_middle"].queryset = EventPart.objects.filter(
                type=EventPart.EventPartTypes.MIDDLE
            ).all()
            self.fields["eventpart_end"].queryset = EventPart.objects.filter(
                type=EventPart.EventPartTypes.END
            ).all()

    eventpart_start = forms.ModelChoiceField(required=False, queryset=None)
    eventpart_middle = forms.ModelChoiceField(required=False, queryset=None)
    eventpart_end = forms.ModelChoiceField(required=False, queryset=None)


class EventpartSettingsForm(SettingsForm):
    eventparts__public = forms.BooleanField(
        label=_("Show Eventparts in customers order view"),
        required=False,
        initial=False,
    )
    eventparts__public_name = I18nFormField(
        label=_("Customer facing name of the eventparts section"),
        required=True,
        widget=I18nTextInput,
        initial=LazyI18nString({"en": "Eventparts"}),
    )
    eventparts__public_description = I18nFormField(
        label=_("Customer facing description of the eventparts"),
        required=False,
        widget=I18nTextarea,
    )
    eventparts__public_start_name = I18nFormField(
        label=_("Name of the first eventpart"),
        required=True,
        initial=LazyI18nString({"en": "Start"}),
        widget=I18nTextInput,
    )
    eventparts__public_middle_name = I18nFormField(
        label=_("Name of the second eventpart"),
        required=True,
        initial=LazyI18nString({"en": "Middle"}),
        widget=I18nTextInput,
    )
    eventparts__public_end_name = I18nFormField(
        label=_("Name of the third eventpart"),
        required=True,
        initial=LazyI18nString({"en": "End"}),
        widget=I18nTextInput,
    )
