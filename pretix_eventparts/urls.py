from django.conf.urls import url

from pretix_eventparts.views import (
    EventPartAssign,
    EventPartCreate,
    EventPartDelete,
    EventPartList,
    EventPartUpdate,
    SettingsView,
)

urlpatterns = [
    url(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/eventparts/parts/",
        EventPartList.as_view(),
        name="eventpart.list",
    ),
    url(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/eventparts/part/(?P<eventpart>\d+)/delete$",
        EventPartDelete.as_view(),
        name="eventpart.delete",
    ),
    url(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/eventparts/part/(?P<eventpart>\d+)/",
        EventPartUpdate.as_view(),
        name="eventpart.edit",
    ),
    url(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/eventparts/part/",
        EventPartCreate.as_view(),
        name="eventpart.create",
    ),
    url(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/eventparts/order/(?P<code>[0-9A-Z]+)/",
        EventPartAssign.as_view(),
        name="eventpart.assign",
    ),
    url(
        r"^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/eventparts/settings$",
        SettingsView.as_view(),
        name="eventpart.settings",
    ),
]
