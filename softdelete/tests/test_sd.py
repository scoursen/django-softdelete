from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.models import ContentType
from softdelete.test_softdelete_app.exceptions import ModelDeletionException
from softdelete.test_softdelete_app.models import (
    TestModelOne,
    TestModelTwoCascade,
    TestModelThree,
    TestModelThrough,
    TestModelTwoDoNothing,
    TestModelTwoSetNull,
    TestModelTwoSetNullOneToOne,
    TestModelO2OFemaleSetNull,
    TestModelBaseO2OMale,
    TestModelO2OFemaleCascade,
    TestModelO2OFemaleCascadeNoSD,
    TestModelO2OFemaleCascadeErrorOnDelete,
    TestGenericRelation,
    TestGenericForeignKey,
)
from softdelete.tests.constanats import TEST_MODEL_ONE_COUNT, TEST_MODEL_TWO_TOTAL_COUNT, TEST_MODEL_THREE_COUNT, \
    TEST_MODEL_TWO_LIST, TEST_MODEL_TWO_CASCADE_COUNT, TEST_MODEL_TWO_SET_NULL_COUNT, TEST_MODEL_TWO_DO_NOTHING_COUNT
from softdelete.models import *
from softdelete.signals import *
import logging

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


class BaseTest(TestCase):
    def setUp(self):
        # update TEST_MODEL_ONE_COUNT constant if you initialize more or less instance of TestModelOne
        self.tmo1 = TestModelOne.objects.create(extra_bool=True)
        self.tmo2 = TestModelOne.objects.create(extra_bool=False)

        for x in range(TEST_MODEL_TWO_TOTAL_COUNT):
            TEST_MODEL_TWO_LIST[x % len(TEST_MODEL_TWO_LIST)] \
                .objects.create(extra_int=x, tmo=self.tmo1 if x % TEST_MODEL_ONE_COUNT else self.tmo2)
        for x in range(TEST_MODEL_TWO_TOTAL_COUNT):
            if x % TEST_MODEL_ONE_COUNT:
                left_side = self.tmo1
            else:
                left_side = self.tmo2
            for x in range(TEST_MODEL_TWO_TOTAL_COUNT):
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
        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.count())

        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.count())

        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.all_with_deleted().count())

        self.tmo1.delete()

        self.assertEquals(TEST_MODEL_ONE_COUNT - 1, TestModelOne.objects.count())
        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT - 2, TestModelTwoCascade.objects.count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.count())
        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.all_with_deleted().count())

    def test_simple_multi_delete(self):
        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.count())

        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.count())

        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.all_with_deleted().count())

        self.tmo1.delete()
        self.tmo2.delete()

        self.assertEquals(TEST_MODEL_ONE_COUNT - 2, TestModelOne.objects.count())
        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT - 4, TestModelTwoCascade.objects.count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.count())

        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.all_with_deleted().count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.all_with_deleted().count())

        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.count())
        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.all_with_deleted().count())


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
        self.assertEquals(TEST_MODEL_ONE_COUNT, TestModelOne.objects.count())
        self.assertEquals(TEST_MODEL_TWO_CASCADE_COUNT, TestModelTwoCascade.objects.count())
        self.assertEquals(TEST_MODEL_TWO_SET_NULL_COUNT, TestModelTwoSetNull.objects.count())
        self.assertEquals(TEST_MODEL_TWO_DO_NOTHING_COUNT, TestModelTwoDoNothing.objects.count())
        self.assertEquals(TEST_MODEL_THREE_COUNT, TestModelThree.objects.count())
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
        self.assertEquals(self.cs_count + 1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count + (TEST_MODEL_THREE_COUNT // 2  # half is assigned by tmo1
                                           + TEST_MODEL_TWO_CASCADE_COUNT // 2  # half assigned to cascade model two
                                           + 1  # tmo1 itself
                                           ), SoftDeleteRecord.objects.count())
        self._posttest()

    def test_hard_delete(self):
        self._pretest()
        tmo_tmp = TestModelOne.objects.create(extra_bool=True)
        tmo_tmp.delete()
        self.assertEquals(self.cs_count + 1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count + 1, SoftDeleteRecord.objects.count())
        tmo_tmp.delete()
        self.assertEquals(self.cs_count, ChangeSet.objects.count())
        self.assertEquals(self.rs_count, SoftDeleteRecord.objects.count())
        self.assertRaises(TestModelOne.DoesNotExist,
                          TestModelOne.objects.get,
                          pk=tmo_tmp.pk)

    def test_filter_delete(self):
        self._pretest()
        TestModelOne.objects.filter(pk=1).delete()
        self.assertEquals(self.cs_count + 1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count + (TEST_MODEL_THREE_COUNT // 2  # half is assigned by tmo1
                                           + TEST_MODEL_TWO_CASCADE_COUNT // 2  # half assigned to cascade model two
                                           + 1  # tmo1 itself
                                           ), SoftDeleteRecord.objects.count())
        self._posttest()

    def test_set_null_on_one_to_one(self):
        """
        Make sure reverse `OneToOne` fields are set to `None` upon soft delete.

        When an instance is soft deleted and other instances have a `OneToOne`
        relation to this instance with `on_delete=SET_NULL`, the other
        instances should have their relation set to `None`.
        """
        # Create two instances, one with a relation to the other.
        to_be_deleted = TestModelOne.objects.create()
        other_with_relation = TestModelTwoSetNullOneToOne.objects.create(
            tmo=to_be_deleted,
            extra_int=0,
        )

        # Make sure the relation is there before soft deleting.
        self.assertEqual(other_with_relation.tmo, to_be_deleted)

        # Then delete the instance and expect the relation from the other
        # instance is now `None`.
        to_be_deleted.delete()
        other_with_relation.refresh_from_db()
        self.assertIsNone(other_with_relation.tmo)

    def test_delete_generic_relation(self):
        test_generic_relation = TestGenericRelation.objects.create()
        test_generic_foreign_key = TestGenericForeignKey.objects.create(
            content_type=ContentType.objects.get_for_model(TestGenericRelation),
            object_id=test_generic_relation.pk,
        )
        test_generic_relation.delete()
        test_generic_foreign_key.refresh_from_db()
        test_generic_relation.refresh_from_db()
        self.assertIsNotNone(test_generic_relation.deleted_at)
        self.assertIsNotNone(test_generic_foreign_key.deleted_at)


class AdminTest(BaseTest):
    def test_admin(self):
        client = Client()
        u = User.objects.create_user(username='test-user', password='test',
                                     email='test-user@example.com')
        u.is_staff = True
        u.is_superuser = True
        u.save()
        self.assertFalse(self.tmo1.deleted)
        client.login(username='test-user', password='test')
        url = '/admin/test_softdelete_app/testmodelone/1/'
        tmo = client.get(url)
        # the admin URLs changed with v1.9 change our expectation if it makes sense version wise.
        if tmo.status_code == 302 and tmo['Location'].endswith('change/') and (1, 9) <= django.VERSION:
            url = tmo['Location']
            tmo = client.get(url)
        self.assertEquals(tmo.status_code, 200)
        tmo = client.post(url, {'extra_bool': '1', 'deleted': '1'})
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
        self.assertEquals(self.cs_count + 1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count + (TEST_MODEL_THREE_COUNT // 2  # half is assigned by tmo1
                                           + TEST_MODEL_TWO_CASCADE_COUNT // 2  # half assigned to cascade model two
                                           + 1  # tmo1 itself
                                           ), SoftDeleteRecord.objects.count())
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
        self.assertEquals(self.cs_count + 1, ChangeSet.objects.count())
        self.assertEquals(self.rs_count + (TEST_MODEL_THREE_COUNT // 2  # half is assigned by tmo1
                                           + TEST_MODEL_TWO_CASCADE_COUNT // 2  # half assigned to cascade model two
                                           + 1  # tmo1 itself
                                           ), SoftDeleteRecord.objects.count())
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


class SoftDeleteRelatedFieldLookupsTests(BaseTest):
    def test_related_foreign_key(self):
        tmt1 = TestModelTwoCascade.objects.create(extra_int=100, tmo=self.tmo1)
        tmt2 = TestModelTwoCascade.objects.create(extra_int=100, tmo=self.tmo2)

        self.assertEquals(self.tmo1.tmts.filter(extra_int=100).count(), 1)
        self.assertEquals(self.tmo1.tmts.filter(extra_int=100)[0].pk, tmt1.pk)
        self.assertEquals(self.tmo2.tmts.filter(extra_int=100).count(), 1)
        self.assertEquals(self.tmo2.tmts.filter(extra_int=100)[0].pk, tmt2.pk)

        self.assertEquals(self.tmo1.tmts.get(extra_int=100), tmt1)
        self.assertEquals(self.tmo2.tmts.get(extra_int=100), tmt2)

        tmt1.delete()
        self.assertEquals(self.tmo1.tmts.filter(extra_int=100).count(), 0)
        tmt1.undelete()
        self.assertEquals(self.tmo1.tmts.filter(extra_int=100).count(), 1)

        tmt1.delete()
        tmt1.delete()
        self.assertRaises(TestModelTwoCascade.DoesNotExist,
                          self.tmo1.tmts.get, extra_int=100)

    def test_related_m2m(self):
        t31 = TestModelThree.objects.create(extra_int=100)
        TestModelThrough.objects.create(tmo1=self.tmo1, tmo3=t31)
        t32 = TestModelThree.objects.create(extra_int=100)
        TestModelThrough.objects.create(tmo1=self.tmo2, tmo3=t32)

        self.assertEquals(self.tmo1.testmodelthree_set.filter(extra_int=100).count(), 1)
        self.assertEquals(self.tmo1.testmodelthree_set.filter(extra_int=100)[0].pk, t31.pk)
        self.assertEquals(self.tmo2.testmodelthree_set.filter(extra_int=100).count(), 1)
        self.assertEquals(self.tmo2.testmodelthree_set.filter(extra_int=100)[0].pk, t32.pk)

        self.assertEquals(self.tmo1.testmodelthree_set.get(extra_int=100), t31)
        self.assertEquals(self.tmo2.testmodelthree_set.get(extra_int=100), t32)

        t31.delete()
        self.assertEquals(self.tmo1.testmodelthree_set.filter(extra_int=100).count(), 0)
        t31.undelete()
        self.assertEquals(self.tmo1.testmodelthree_set.filter(extra_int=100).count(), 1)

        t31.delete()
        t31.delete()
        self.assertRaises(TestModelThree.DoesNotExist,
                          self.tmo1.testmodelthree_set.get, extra_int=100)

    def test_one_to_one(self):
        bob = TestModelBaseO2OMale.objects.create(name='Bob')
        alice = TestModelO2OFemaleSetNull.objects.create(name='Alice', link=bob)

        bob.delete()

        self.assertEquals(alice.link_id, None)

        romeo = TestModelBaseO2OMale.objects.create(name='Romeo')
        juliet = TestModelO2OFemaleCascade.objects.create(name='Juliet', link=romeo)

        romeo.delete()

        self.assertRaises(TestModelO2OFemaleCascade.DoesNotExist, TestModelO2OFemaleCascade.objects.get, name='Juliet')
        self.assertEquals(juliet.deleted, True)

        kurt = TestModelBaseO2OMale.objects.create(name='Kurt')
        courtney = TestModelO2OFemaleCascadeNoSD.objects.create(name='Courtney', link=kurt)
        jack = TestModelBaseO2OMale.objects.create(name='Jack')
        jill = TestModelO2OFemaleCascadeNoSD.objects.create(name='jill', link=jack)

        kurt.delete()

        self.assertTrue(TestModelO2OFemaleCascadeNoSD.objects.filter(id=jill.id).exists())
        self.assertFalse(TestModelO2OFemaleCascadeNoSD.objects.filter(id=courtney.id).exists())

    @override_settings(SOFTDELETE_CASCADE_ALLOW_DELETE_ALL=True)
    def test_fallback_delete_all_setting_false(self):
        bob = TestModelBaseO2OMale.objects.create(name='Bob')
        TestModelO2OFemaleCascadeErrorOnDelete.objects.create(name='Alice', link=bob)

        romeo = TestModelBaseO2OMale.objects.create(name='Romeo')
        TestModelO2OFemaleCascadeErrorOnDelete.objects.create(name='Juliet', link=romeo)

        self.assertFalse(TestModelO2OFemaleCascadeErrorOnDelete.objects.all().exists())

    @override_settings(SOFTDELETE_CASCADE_ALLOW_DELETE_ALL=False)
    def test_fallback_delete_all_setting_false(self):
        bob = TestModelBaseO2OMale.objects.create(name='Bob')
        alice = TestModelO2OFemaleCascadeErrorOnDelete.objects.create(name='Alice', link=bob)

        romeo = TestModelBaseO2OMale.objects.create(name='Romeo')
        TestModelO2OFemaleCascadeErrorOnDelete.objects.create(name='Juliet', link=romeo)

        self.assertRaises(ModelDeletionException, alice.delete)
        self.assertTrue(TestModelO2OFemaleCascadeErrorOnDelete.objects.filter(id=alice.id).exists())
        self.assertEquals(TestModelO2OFemaleCascadeErrorOnDelete.objects.count(), 2)
