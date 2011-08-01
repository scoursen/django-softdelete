from django.db import models
from softdelete.models import SoftDeleteObject

class TestModelOne(SoftDeleteObject):
    extra_bool = models.BooleanField(default=False)
    
    def __unicode__(self):
        return u"TestModelOne - extra_bool: %s" % self.extra_bool
    
class TestModelTwo(SoftDeleteObject):
    extra_int = models.IntegerField()
    tmo = models.ForeignKey(TestModelOne,related_name='tmos')
    
    def __unicode__(self):
        return u"TestModelTwo - extra_int: %s, tmo: %s" % (self.extra_int,
                                                           self.tmo)


