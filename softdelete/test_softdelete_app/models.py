from django.db import models
from django.contrib import admin
from django.db.models import QuerySet

from softdelete.models import *
from softdelete.admin import *
from softdelete.test_softdelete_app.exceptions import ModelDeletionException


class TestModelOne(SoftDeleteObject):
    extra_bool = models.BooleanField(default=False)


class TestModelTwoCascade(SoftDeleteObject):
    extra_int = models.IntegerField()
    tmo = models.ForeignKey(
        TestModelOne,
        on_delete=models.CASCADE,
        related_name='tmts'
    )


class TestModelTwoDoNothing(SoftDeleteObject):
    extra_int = models.IntegerField()
    tmo = models.ForeignKey(
        TestModelOne,
        on_delete=models.DO_NOTHING,
        related_name='tmdn'
    )


class TestModelTwoSetNull(SoftDeleteObject):
    extra_int = models.IntegerField()
    tmo = models.ForeignKey(
        TestModelOne,
        on_delete=models.SET_NULL,
        related_name='tmsn',
        null=True,
        blank=True
    )


class TestModelTwoSetNullOneToOne(SoftDeleteObject):
    extra_int = models.IntegerField()
    tmo = models.OneToOneField(
        TestModelOne,
        on_delete=models.SET_NULL,
        related_name='tmsno',
        null=True,
        blank=True
    )


class TestModelThree(SoftDeleteObject):
    tmos = models.ManyToManyField(TestModelOne, through='TestModelThrough')
    extra_int = models.IntegerField(blank=True, null=True)


class TestModelThrough(SoftDeleteObject):
    tmo1 = models.ForeignKey(
        TestModelOne,
        on_delete=models.CASCADE,
        related_name="left_side"
    )
    tmo3 = models.ForeignKey(
        TestModelThree,
        on_delete=models.CASCADE,
        related_name='right_side'
    )


class TestModelBaseO2OMale(SoftDeleteObject):
    name = models.CharField(max_length=16)


class TestModelO2OFemaleSetNull(SoftDeleteObject):
    name = models.CharField(max_length=16)
    link = models.OneToOneField(
        TestModelBaseO2OMale,
        related_name='one_to_one_set_null',
        on_delete=models.SET_NULL,
        null=True,
    )


class TestModelO2OFemaleCascade(SoftDeleteObject):
    name = models.CharField(max_length=16)
    link = models.OneToOneField(
        TestModelBaseO2OMale,
        related_name='one_to_one_cascade',
        on_delete=models.CASCADE,
    )


class TestModelO2OFemaleCascadeErrorOnDelete(models.Model):
    name = models.CharField(max_length=16)
    link = models.OneToOneField(
        TestModelBaseO2OMale,
        related_name='one_to_one_cascade_error_on_delete',
        on_delete=models.CASCADE,
    )

    def delete(self, using=None, keep_parents=False):
        raise ModelDeletionException("Preventing deletion!")


class TestModelO2OFemaleCascadeNoSD(models.Model):
    name = models.CharField(max_length=16)
    link = models.OneToOneField(
        TestModelBaseO2OMale,
        related_name='one_to_one_cascade_no_sd',
        on_delete=models.CASCADE
    )


admin.site.register(TestModelOne, SoftDeleteObjectAdmin)
admin.site.register(TestModelTwoCascade, SoftDeleteObjectAdmin)
admin.site.register(TestModelTwoSetNull, SoftDeleteObjectAdmin)
admin.site.register(TestModelTwoDoNothing, SoftDeleteObjectAdmin)

admin.site.register(TestModelThree, SoftDeleteObjectAdmin)
admin.site.register(TestModelThrough, SoftDeleteObjectAdmin)
