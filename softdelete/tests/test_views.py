from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db import models
from softdelete.test_softdelete_app.models import TestModelOne, TestModelTwo
from softdelete.models import *
from softdelete.signals import *
import logging

class ViewBase(TestCase):
    def setUp(self):
        u, c = User.objects.get_or_create(username="undelete_test")
        u.is_active = True
        u.set_password("undelete_password")
        gr = create_group()
        if USE_SOFTDELETE_GROUP:
            gr = Group.objects.get(name="Softdelete User")
            u.groups.add(gr)
            u.save()
            gr.save()
        else:
            assign_permissions(u)
        u.save()
        self.tmo1 = TestModelOne.objects.create(extra_bool=True)
        for x in range(10):
            TestModelTwo.objects.create(extra_int=x, tmo=self.tmo1)
        self.tmo2 = TestModelOne.objects.create(extra_bool=False)
        for x in range(10):
            TestModelTwo.objects.create(extra_int=x*x, tmo=self.tmo2)
        self.tmo2.delete()

class ViewTest(ViewBase):
    def __init__(self, *args, **kwargs):
        settings.USE_SOFTDELETE_GROUP = kwargs.get('USE_SOFTDELETE_GROUP', False)
        if kwargs.has_key('USE_SOFTDELETE_GROUP'):
            del kwargs['USE_SOFTDELETE_GROUP']
        super(ViewTest, self).__init__(*args, **kwargs)

    def setUp(self):
        super(ViewTest, self).setUp()
        self.client = Client()
        self.client.login(username="undelete_test",
                          password="undelete_password")

    def test_authorization(self):
        rv = self.client.get(reverse("softdelete.changeset.list"))
        pk = ChangeSet.objects.latest('created_date').pk
        for view_name in [reverse("softdelete.changeset.list"),
                          reverse("softdelete.changeset.view", args=(pk,)),
                          reverse("softdelete.changeset.undelete", args=(pk,)),]:
            cli2 = Client()
            rv = cli2.get(view_name)
            self.assertEquals(rv.status_code, 302)
            self.assertTrue((settings.DOMAIN + reverse('auth_login')) in rv['Location'])
            self.assertEquals(cli2.get(rv['Location']).status_code,
                              200)
            cli2.login(username='undelete_test', password='undelete_password')
            rv = cli2.get(view_name)
            self.assertEquals(rv.status_code, 200)

    def test_undelete(self):
        self.cs_count = ChangeSet.objects.count()
        self.rs_count = SoftDeleteRecord.objects.count()
        self.t_count = TestModelOne.objects.count()
        self.tmo1.delete()
        self.assertEquals(self.t_count-1, TestModelOne.objects.count())
        self.assertEquals(0, self.tmo1.tmos.count())
        self.assertEquals(self.cs_count+1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count+11, SoftDeleteRecord.objects.count())
        rv = self.client.get(reverse("softdelete.changeset.undelete",
                                     args=(ChangeSet.objects.latest("created_date").pk,)))
        self.assertEquals(rv.status_code,200)
        rv = self.client.post(reverse("softdelete.changeset.undelete", 
                                     args=(ChangeSet.objects.latest("created_date").pk,)),
                             {'action': 'Undelete'})
        self.assertEquals(rv.status_code, 302)
        rv = self.client.get(rv['Location'])
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(self.cs_count, ChangeSet.objects.count())
        self.assertEquals(self.rs_count, SoftDeleteRecord.objects.count())
        self.assertEquals(self.t_count, TestModelOne.objects.count())
        self.assertEquals(10, self.tmo1.tmos.count())

class GroupViewTest(ViewTest):
    def __init__(self, *args, **kwargs):
        super(GroupViewTest, self).__init__(USE_SOFTDELETE_GROUP=True, *args, **kwargs)
