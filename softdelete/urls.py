from django.conf.urls.defaults import *
from softdelete.views import *

urlpatterns = patterns('softdelete.views',
                       url(r'^changeset/(?P<changeset_pk>\d+?)/undelete/$',
                           ChangeSetUpdate.as_view(),
                           name="softdelete.changeset.undelete"), 
                       url(r'^changeset/(?P<changeset_pk>\d+?)/$',
                           ChangeSetDetail.as_view(),
                           name="softdelete.changeset.view"),
                       url(r'^changeset/$',
                           ChangeSetList.as_view(),
                           name="softdelete.changeset.list"),
                       )

