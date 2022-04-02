from django.db import models
from django.contrib import admin
from softdelete.models import *
from softdelete.admin import *


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


admin.site.register(TestModelOne, SoftDeleteObjectAdmin)
admin.site.register(TestModelTwoCascade, SoftDeleteObjectAdmin)
admin.site.register(TestModelTwoSetNull, SoftDeleteObjectAdmin)
admin.site.register(TestModelTwoDoNothing, SoftDeleteObjectAdmin)

admin.site.register(TestModelThree, SoftDeleteObjectAdmin)
admin.site.register(TestModelThrough, SoftDeleteObjectAdmin)
