from django.conf import settings
from django.db.models import loading, query
from django.core.management import call_command
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db import models
from softdelete.test_softdelete_app.models import TestModelOne, TestModelTwo, TestModelThree, TestModelThrough
from softdelete.models import *
from softdelete.signals import *
import logging

class BaseTest(TestCase):
    def setUp(self):
        self.tmo1 = TestModelOne.objects.create(extra_bool=True)
        self.tmo2 = TestModelOne.objects.create(extra_bool=False)
        for x in range(10):
            if x % 2:
                parent = self.tmo1
            else:
                parent = self.tmo2
            TestModelTwo.objects.create(extra_int=x, tmo=parent)
        for x in range(10):
            if x % 2:
                left_side = self.tmo1
            else:
                left_side = self.tmo2
            for x in range(10):
                t3 = TestModelThree.objects.create()
                tmt = TestModelThrough.objects.create(tmo1=left_side, tmo3=t3)
        self.user = User.objects.create_user(username='SoftdeleteUser',
                                             password='SoftdeletePassword',
                                             email='softdeleteuser@example.com')
        gr = create_group()
        if USE_SOFTDELETE_GROUP:
            gr = Group.objects.get(name="Softdelete User")
            self.user.groups.add(gr)
            self.user.save()
            gr.save()
        else:
            assign_permissions(self.user)
        self.user.save()
        self.unauthorized = User.objects.create_user(username='NonSoftdeleteUser',
                                                     password='NonSoftdeletePassword',
                                                     email='nonsoftdeleteuser@example.com')


class InitialTest(BaseTest):

    def test_simple_delete(self):
        self.assertEquals(2, TestModelOne.objects.count())
        self.assertEquals(10, TestModelTwo.objects.count())
        self.assertEquals(2,
                          TestModelOne.objects.all_with_deleted().count())
        self.assertEquals(10,
                          TestModelTwo.objects.all_with_deleted().count())
        self.tmo1.delete()
        self.assertEquals(1, TestModelOne.objects.count())
        self.assertEquals(5, TestModelTwo.objects.count())
        self.assertEquals(2,
                          TestModelOne.objects.all_with_deleted().count())
        self.assertEquals(10,
                          TestModelTwo.objects.all_with_deleted().count())

class DeleteTest(BaseTest):
    def pre_delete(self, *args, **kwargs):
        self.pre_delete_called = True

    def post_delete(self, *args, **kwargs):
        self.post_delete_called = True

    def pre_soft_delete(self, *args, **kwargs):
        self.pre_soft_delete_called = True
        
    def post_soft_delete(self, *args, **kwargs):
        self.post_soft_delete_called = True

    def _pretest(self):
        self.pre_delete_called = False
        self.post_delete_called = False
        self.pre_soft_delete_called = False
        self.post_soft_delete_called = False
        models.signals.pre_delete.connect(self.pre_delete)
        models.signals.post_delete.connect(self.post_delete)
        pre_soft_delete.connect(self.pre_soft_delete)
        post_soft_delete.connect(self.post_soft_delete)
        self.assertEquals(2, TestModelOne.objects.count())
        self.assertEquals(10, TestModelTwo.objects.count())
        self.assertFalse(self.tmo1.deleted)
        self.assertFalse(self.pre_delete_called)
        self.assertFalse(self.post_delete_called)
        self.assertFalse(self.pre_soft_delete_called)
        self.assertFalse(self.post_soft_delete_called)
        self.cs_count = ChangeSet.objects.count()
        self.rs_count = SoftDeleteRecord.objects.count()

    def _posttest(self):
        self.tmo1 = TestModelOne.objects.get(pk=self.tmo1.pk)
        self.tmo2 = TestModelOne.objects.get(pk=self.tmo2.pk)
        self.assertTrue(self.tmo1.deleted)
        self.assertFalse(self.tmo2.deleted)
        self.assertTrue(self.pre_delete_called)
        self.assertTrue(self.post_delete_called)
        self.assertTrue(self.pre_soft_delete_called)
        self.assertTrue(self.post_soft_delete_called)
        self.tmo1.undelete()
        
    def test_delete(self):
        self._pretest()
        self.tmo1.delete()
        self.assertEquals(self.cs_count+1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count+56, SoftDeleteRecord.objects.count()) 
        self._posttest()

    def test_filter_delete(self):
        self._pretest()
        TestModelOne.objects.filter(pk=1).delete()
        self.assertEquals(self.cs_count+1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count+56, SoftDeleteRecord.objects.count())
        self._posttest()

class AdminTest(BaseTest):
    def test_admin(self):
        client = Client()
        u = User.objects.create_user(username='test-user', password='test',
                                     email='test-user@example.com')
        u.is_staff = True
        u.is_superuser = True
        u.save()
        client.login(username='test-user', password='test')
        tmo = client.get('/admin/test_softdelete_app/testmodelone/1/')
        self.assertEquals(tmo.status_code, 200)
        tmo = client.post('/admin/test_softdelete_app/testmodelone/1/',
                          {'extra_bool': '1', 'deleted': '1'})
        self.assertEquals(tmo.status_code, 302)
        self.tmo1 = TestModelOne.objects.get(pk=self.tmo1.pk)
        self.assertTrue(self.tmo1.deleted)

class AuthorizationTest(BaseTest):
    def test_permission_needed(self):
        cl = Client()
        cl.login(username='NonSoftdeleteUser',
                 password='NonSoftdeletePassword')
        rv = cl.get(reverse('softdelete.changeset.list'))
        self.assertEquals(rv.status_code, 302)
        rv = cl.get(reverse('softdelete.changeset.view', args=(1,)))
        self.assertEquals(rv.status_code, 302)
        rv = cl.get(reverse('softdelete.changeset.undelete', args=(1,)))
        self.assertEquals(rv.status_code, 302)

class UndeleteTest(BaseTest):
    def pre_undelete(self, *args, **kwargs):
        self.pre_undelete_called = True
        
    def post_undelete(self, *args, **kwargs):
        self.post_undelete_called = True

    def test_undelete(self):
        self.pre_undelete_called = False
        self.post_undelete_called = False
        pre_undelete.connect(self.pre_undelete)
        post_undelete.connect(self.post_undelete)
        self.assertFalse(self.pre_undelete_called)
        self.assertFalse(self.post_undelete_called)
        self.cs_count = ChangeSet.objects.count()
        self.rs_count = SoftDeleteRecord.objects.count()
        self.tmo1.delete()
        self.assertEquals(self.cs_count+1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count+56, SoftDeleteRecord.objects.count())
        self.tmo1 = TestModelOne.objects.get(pk=self.tmo1.pk)
        self.tmo2 = TestModelOne.objects.get(pk=self.tmo2.pk)
        self.assertTrue(self.tmo1.deleted)
        self.assertFalse(self.tmo2.deleted)
        self.tmo1.undelete()
        self.assertEquals(0, ChangeSet.objects.count())
        self.assertEquals(0, SoftDeleteRecord.objects.count())
        self.tmo1 = TestModelOne.objects.get(pk=self.tmo1.pk)
        self.tmo2 = TestModelOne.objects.get(pk=self.tmo2.pk)
        self.assertFalse(self.tmo1.deleted)
        self.assertFalse(self.tmo2.deleted)
        self.assertTrue(self.pre_undelete_called)
        self.assertTrue(self.post_undelete_called)

        self.tmo1.delete()
        self.assertEquals(self.cs_count+1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count+56, SoftDeleteRecord.objects.count())
        self.tmo1 = TestModelOne.objects.get(pk=self.tmo1.pk)
        self.tmo2 = TestModelOne.objects.get(pk=self.tmo2.pk)
        self.assertTrue(self.tmo1.deleted)
        self.assertFalse(self.tmo2.deleted)
        TestModelOne.objects.deleted_set().undelete()
        self.assertEquals(0, ChangeSet.objects.count())
        self.assertEquals(0, SoftDeleteRecord.objects.count())
        self.tmo1 = TestModelOne.objects.get(pk=self.tmo1.pk)
        self.tmo2 = TestModelOne.objects.get(pk=self.tmo2.pk)
        self.assertFalse(self.tmo1.deleted)
        self.assertFalse(self.tmo2.deleted)
        self.assertTrue(self.pre_undelete_called)
        self.assertTrue(self.post_undelete_called)

class M2MTests(BaseTest):
    def test_m2mdelete(self):
        t3 = TestModelThree.objects.all()[0]
        self.assertFalse(t3.deleted)
        for x in t3.tmos.all():
            self.assertFalse(x.deleted)
        t3.delete()
        for x in t3.tmos.all():
            self.assertFalse(x.deleted)



