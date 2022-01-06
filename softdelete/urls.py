from django.urls import include, re_path
from softdelete.views import *

urlpatterns = [
    re_path(r'^changeset/(?P<changeset_pk>\d+?)/undelete/$',
        ChangeSetUpdate.as_view(),
        name="softdelete.changeset.undelete"),
    re_path(r'^changeset/(?P<changeset_pk>\d+?)/$',
        ChangeSetDetail.as_view(),
        name="softdelete.changeset.view"),
    re_path(r'^changeset/$',
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
        urlpatterns.append(re_path(r'^admin/', include(admin.site.urls)))
        urlpatterns.append(re_path(r'^accounts/', include('django.contrib.auth.urls')))
