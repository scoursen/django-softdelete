from django.conf.urls import url, include
from softdelete.views import *

urlpatterns = [
    url(r'^changeset/(?P<changeset_pk>\d+?)/undelete/$',
        ChangeSetUpdate.as_view(),
        name="softdelete.changeset.undelete"),
    url(r'^changeset/(?P<changeset_pk>\d+?)/$',
        ChangeSetDetail.as_view(),
        name="softdelete.changeset.view"),
    url(r'^changeset/$',
        ChangeSetList.as_view(),
        name="softdelete.changeset.list"),
]

import sys
if 'test' in sys.argv:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns.append(url(r'^admin/', include(admin.site.urls)))
