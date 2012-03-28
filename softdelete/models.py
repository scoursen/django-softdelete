from django.conf import settings
from django.db.models import query
from django.db import models
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group, Permission
import hashlib
from datetime import datetime
import logging
from softdelete.signals import *

try:
    USE_SOFTDELETE_GROUP = settings.USE_SOFTDELETE_GROUP
except:
    USE_SOFTDELETE_GROUP = False

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
    def all_with_deleted(self):
        qs = super(SoftDeleteQuerySet, self).all()
        qs.__class__ = SoftDeleteQuerySet
        return qs
    
    def delete(self, using='default', *args, **kwargs):
        if not len(self):
            return
        cs = kwargs.get('changeset')
        logging.debug("STARTING QUERYSET SOFT-DELETE: %s. %s" % (self, len(self)))
        for obj in self:
            rs, c = SoftDeleteRecord.objects.get_or_create(changeset=cs or _determine_change_set(obj),
                                                           content_type=ContentType.objects.get_for_model(obj),
                                                           object_id=obj.pk)
            logging.debug(" -----  CALLING delete() on %s" % obj)
            obj.delete(using, *args, **kwargs)        


    def undelete(self, using='default', *args, **kwargs):
        logging.debug("UNDELETING %s" % self)
        for obj in self:
            cs = _determine_change_set(obj)
            cs.undelete()
        logging.debug("FINISHED UNDELETING %s" %self)

class SoftDeleteManager(models.Manager):
    def get_query_set(self):
        qs = super(SoftDeleteManager,self).get_query_set().filter(deleted_at__isnull=1)
        qs.__class__ = SoftDeleteQuerySet
        return qs

    def all_with_deleted(self, prt=False):
        if hasattr(self, 'core_filters'): # it's a RelatedManager
            qs = super(SoftDeleteManager, self).get_query_set().filter(**self.core_filters)
        else:
            qs = super(SoftDeleteManager, self).get_query_set()
        qs.__class__ = SoftDeleteQuerySet
        return qs

    def deleted_set(self):
        qs = super(SoftDeleteManager, self).get_query_set().filter(deleted_at__isnull=0)
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
    deleted_at = models.DateTimeField(blank=True, null=True, default=None)
    objects = SoftDeleteManager()
    class Meta:
        abstract = True
        permissions = (
            ('can_undelete', 'Can undelete this object'),
            )
        
    def __init__(self, *args, **kwargs):
        super(SoftDeleteObject, self).__init__(*args, **kwargs)
        self.__dirty = False

    def get_deleted(self):
        return self.deleted_at != None

    def set_deleted(self, d):
        """Called via the admin interface (if user checks the "deleted" checkox)"""
        if d and not self.deleted_at:
            self.__dirty = True
            self.deleted_at = datetime.utcnow()
        elif not d and self.deleted_at:
            self.__dirty = True
            self.deleted_at = None

    deleted = property(get_deleted, set_deleted)

    def _do_delete(self, changeset, related):
        rel = related.get_accessor_name()
        try:
            getattr(self, rel).all().delete(changeset=changeset)
        except:
            try:
                getattr(self, rel).all().delete()
            except:
                try:
                    getattr(self, rel).__class__.objects.all().delete(changeset=changeset)
                except:
                    getattr(self, rel).__class__.objects.all().delete()

    def delete(self, *args, **kwargs):
        if self.deleted_at:
            logging.debug("HARD DELETEING type %s, %s" % (type(self), self))
            try:
                cs = ChangeSet.objects.get(content_type=ContentType.objects.get_for_model(self),
                                           object_id=self.pk)
                cs.delete()
                super(SoftDeleteObject, self).delete(*args, **kwargs)
            except:
                try:    
                    cs = kwargs.get('changeset') or _determine_change_set(self)
                    rs = SoftDeleteRecord.objects.get(changeset=cs,
                                                      content_type=ContentType.objects.get_for_model(self),
                                                      object_id=self.pk)
                    if rs.changeset.soft_delete_records.count() == 1:
                        cs.delete()
                    else:
                        rs.delete()
                    super(SoftDeleteObject, self).delete(*args, **kwargs)
                except:
                    pass
        else:
            using = kwargs.get('using', settings.DATABASES['default'])
            models.signals.pre_delete.send(sender=self.__class__, 
                                           instance=self, 
                                           using=using)
            pre_soft_delete.send(sender=self.__class__,
                                 instance=self,
                                 using=using)
            logging.debug('SOFT DELETING type: %s, %s' % (type(self), self))
            cs = kwargs.get('changeset') or _determine_change_set(self)
            SoftDeleteRecord.objects.get_or_create(changeset=cs,
                                                   content_type=ContentType.objects.get_for_model(self),
                                                   object_id=self.pk)
            self.deleted_at = datetime.today()
            self.save()
            for x in self._meta.get_all_related_objects():
                self._do_delete(cs, x)
            logging.debug("FINISHED SOFT DELETING RELATED %s" % self)
            models.signals.post_delete.send(sender=self.__class__, 
                                            instance=self, 
                                            using=using)
            post_soft_delete.send(sender=self.__class__,
                                  instance=self,
                                  using=using)

    def _do_undelete(self, using='default'):
        pre_undelete.send(sender=self.__class__,
                          instance=self,
                          using=using)
        self.deleted_at = None
        self.save()
        post_undelete.send(sender=self.__class__,
                           instance=self,
                           using=using)

    def undelete(self, using='default', *args, **kwargs):
        logging.debug('UNDELETING %s' % self)
        cs = kwargs.get('changeset') or _determine_change_set(self, False)
        cs.undelete(using)
        logging.debug('FINISHED UNDELETING RELATED %s' % self)

    def save(self, **kwargs):
        super(SoftDeleteObject, self).save(**kwargs)
        if self.__dirty:
            self.__dirty = False
            if not self.deleted:
                self.undelete()
            else:
                self.delete()


class ChangeSet(models.Model):
    created_date = models.DateTimeField(default=datetime.utcnow)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    record = generic.GenericForeignKey('content_type', 'object_id')

    def get_content(self):
        self.record = self.content_type.model_class().objects.get(pk=self.object_id)
        return self.record

    def set_content(self, obj):
        self.record = obj

    def undelete(self, using='default'):
        logging.debug("CHANGESET UNDELETE: %s" % self)
        self.content._do_undelete(using)
        for related in self.soft_delete_records.all():
            related.undelete(using)
        self.delete()
        logging.debug("FINISHED CHANGESET UNDELETE: %s" % self)

    def __unicode__(self):
        return 'Changeset: %s, %s' % (self.created_date, self.record)

    content = property(get_content, set_content)

class SoftDeleteRecord(models.Model):
    changeset = models.ForeignKey(ChangeSet, related_name='soft_delete_records')
    created_date = models.DateTimeField(default=datetime.utcnow)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    record = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together= (('changeset', 'content_type', 'object_id'),)

    def get_content(self):
        self.record = self.content_type.model_class().objects.get(pk=self.object_id)
        return self.record

    def set_content(self, obj):
        self.record = obj
    
    def undelete(self, using='default'):
        self.content._do_undelete(using)

    def __unicode__(self):
        return u'SoftDeleteRecord: (%s), (%s/%s), %s' % (self.content,
                                                  self.content_type,
                                                  self.object_id,
                                                  self.changeset.created_date)

    content = property(get_content, set_content)


def assign_permissions(user_or_group):
    for model in ['ChangeSet', 'SoftDeleteRecord']:
        ct = ContentType.objects.get(app_label="softdelete",
                                     model=model.lower())
        p, pc = Permission.objects.get_or_create(name="Can undelete a soft-deleted object",
                                                 codename="can_undelete",
                                                 content_type=ct)
        permissions = [p]
        for permission in ['add_%s' % model.lower(),
                           'change_%s' % model.lower(),
                           'delete_%s' % model.lower(),
                           'can_undelete']:
            for perm_obj in Permission.objects.filter(codename=permission):
                permissions.append(perm_obj)
        perm_list = getattr(user_or_group, 'permissions', 
                            getattr(user_or_group, 'user_permissions'))
        [perm_list.add(x) for x in permissions]
        user_or_group.save()
    return user_or_group

def create_group():
    if USE_SOFTDELETE_GROUP:
        gr, cr = Group.objects.get_or_create(name='Softdelete User')
        if cr:
            assign_permissions(gr)
        return gr
