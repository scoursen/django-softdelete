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
    import django
    from django.contrib import admin
    admin.autodiscover()

    if django.VERSION[0] >= 2:
        from django.urls import path
        urlpatterns.append(path('admin/', admin.site.urls))
        urlpatterns.append(path('accounts/', include('django.contrib.auth.urls')))
    else:
        urlpatterns.append(url(r'^admin/', include(admin.site.urls)))
        urlpatterns.append(url(r'^accounts/', include('django.contrib.auth.urls')))
