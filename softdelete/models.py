from django.conf import settings
from django.db.models import query
from django.db import models
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import hashlib
from datetime import datetime
import logging
from softdelete.signals import *

def _determine_change_set(obj, create=True):
    try:
        qs = SoftDeleteRecord.objects.filter(content_type=ContentType.objects.get_for_model(obj),
                                      object_id=obj.pk).latest('created_date').changeset
        logging.debug("Found changeset via latest recordset")
    except:
        try:
            qs = ChangeSet.objects.filter(content_type=ContentType.objects.get_for_model(obj),
                                          object_id=obj.pk).latest('created_date')
            logging.debug("Found changeset")
        except:
            if create:
                qs = ChangeSet.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                              object_id=obj.pk)
                logging.debug("Creating changeset")
            else:
                logging.debug("Raising ObjectDoesNotExist")
                raise ObjectDoesNotExist
    return qs

class SoftDeleteQuerySet(query.QuerySet):
    def delete(self, using=settings.DATABASES['default'], *args, **kwargs):
        models.signals.pre_delete.send(sender=self.__class__, 
                                       instance=self, 
                                       using=using)
        pre_soft_delete.send(sender=self.__class__,
                             instance=self,
                             using=using)
        cs = kwargs.get('changeset')
        for obj in self:
            rs, c = SoftDeleteRecord.objects.get_or_create(changeset=cs or _determine_change_set(obj),
                                                    content_type=ContentType.objects.get_for_model(obj),
                                                    object_id=obj.pk)
            obj.delete(using, *args, **kwargs)
        logging.debug('SOFT DELETING %s' % self)
        models.signals.post_delete.send(sender=self.__class__, 
                                        instance=self, 
                                        using=using)
        post_soft_delete.send(sender=self.__class__,
                              instance=self,
                              using=using)

    def undelete(self, using=settings.DATABASES['default'], *args, **kwargs):
        logging.debug("UNDELETING %s" % self)
        for obj in self:
            cs = _determine_change_set(obj)
            cs.undelete()
        logging.debug("FINISHED UNDELETING %s" %self)


class SoftDeleteManager(models.Manager):
    def get_query_set(self):
        qs = super(SoftDeleteManager,self).get_query_set().filter(deleted=False)
        qs.__class__ = SoftDeleteQuerySet
        return qs

    def all_with_deleted(self):
        qs = super(SoftDeleteManager, self).get_query_set()
        qs.__class__ = SoftDeleteQuerySet
        return qs

    def deleted_set(self):
        qs = super(SoftDeleteManager, self).get_query_set().filter(deleted=True)
        qs.__class__ = SoftDeleteQuerySet
        return qs

    def get(self, *args, **kwargs):
        return self.all_with_deleted().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        if 'pk' in kwargs:
            qs = self.all_with_deleted().filter(*args, **kwargs)
        else:
            qs = self.get_query_set().filter(*args, **kwargs)
        qs.__class__ = SoftDeleteQuerySet
        return qs

class SoftDeleteObject(models.Model):
    deleted = models.BooleanField(default=False)
#    admin = models.Manager()
    objects = SoftDeleteManager()
    class Meta:
        abstract = True

    def _do_delete(self, changeset, related):
        rel = related.get_accessor_name()
        try:            
            try:
                getattr(self, rel).all().delete(changeset=changeset)
            except:
                getattr(self, rel).all().delete()
        except Exception, e:
            logging.debug("Exception: %s" % e)
            logging.debug('Non-related set DELETE %s' % getattr(self, rel))
            try:
                getattr(self, rel).delete(changeset=changeset)
            except:
                getattr(self, rel).delete()

    def delete(self, using=settings.DATABASES['default'], *args, **kwargs):
        models.signals.pre_delete.send(sender=self.__class__, 
                                       instance=self, 
                                       using=using)
        pre_soft_delete.send(sender=self.__class__,
                             instance=self,
                             using=using)
        logging.debug('SOFT DELETING %s' % self)
        cs = kwargs.get('changeset') or _determine_change_set(self)
        SoftDeleteRecord.objects.get_or_create(changeset=cs,
                                        content_type=ContentType.objects.get_for_model(self),
                                        object_id=self.pk)                                        
        self.deleted = True
        self.save()
        [self._do_delete(cs, x) for x in self._meta.get_all_related_objects()]
        [self._do_delete(cs, x) for x in self._meta.get_all_related_many_to_many_objects()]
        logging.debug("FINISHED SOFT DELETING RELATED %s" % self)
        models.signals.post_delete.send(sender=self.__class__, 
                                        instance=self, 
                                        using=using)
        post_soft_delete.send(sender=self.__class__,
                              instance=self,
                              using=using)

    def _undelete(self, using=settings.DATABASES['default']):
        pre_undelete.send(sender=self.__class__,
                          instance=self,
                          using=using)
        self.deleted = False
        self.save()
        post_undelete.send(sender=self.__class__,
                           instance=self,
                           using=using)

    def undelete(self, using=settings.DATABASES['default'], *args, **kwargs):
        logging.debug('UNDELETING %s' % self)
        cs = kwargs.get('changeset') or _determine_change_set(self, False)
        cs.undelete(using)
        logging.debug('FINISHED UNDELETING RELATED %s' % self)
        
class ChangeSet(models.Model):
    created_date = models.DateTimeField(default=datetime.utcnow)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    record = generic.GenericForeignKey('content_type', 'object_id')

    def get_content(self):
        self.record = self.content_type.model_class().objects.get(pk=self.object_id)
        return self.record

    def undelete(self, using=settings.DATABASES['default']):
        logging.debug("CHANGESET UNDELETE: %s" % self)
        self.content._undelete(using)
        for related in self.recordsets.all():
            related.undelete(using)
        self.delete()
        logging.debug("FINISHED CHANGESET UNDELETE: %s" % self)

    def __unicode__(self):
        import StringIO
        sio = StringIO.StringIO()
        sio.write(u'ChangeSet: %s' % (self.created_date))
        [sio.write(u'\n\t%s' % x) for x in self.recordsets.all()]
        return sio.getvalue()

    content = property(get_content)

class SoftDeleteRecord(models.Model):
    changeset = models.ForeignKey(ChangeSet, related_name='recordsets')
    created_date = models.DateTimeField(default=datetime.utcnow)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    record = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together= (('changeset', 'content_type', 'object_id'),)

    def get_content(self):
        self.record = self.content_type.model_class().objects.get(pk=self.object_id)
        return self.record

    def undelete(self, using=settings.DATABASES['default']):
        self.content._undelete(using)

    def __unicode__(self):
        return u'SoftDeleteRecord: (%s), (%s/%s), %s' % (self.content,
                                                  self.content_type,
                                                  self.object_id,
                                                  self.changeset.created_date)

    content = property(get_content)
