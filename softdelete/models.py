from __future__ import unicode_literals

import django

from django.conf import settings
from django.db.models import query
from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
import logging
from softdelete.signals import *

try:
    USE_SOFTDELETE_GROUP = settings.USE_SOFTDELETE_GROUP
except:
    USE_SOFTDELETE_GROUP = False


def _determine_change_set(obj, create=True):
    try:
        qs = SoftDeleteRecord.objects.filter(content_type=ContentType.objects.get_for_model(obj),
                                             object_id=str(obj.pk)).latest('created_date').changeset
        logging.debug("Found changeset via latest recordset")
    except:
        try:
            qs = ChangeSet.objects.filter(content_type=ContentType.objects.get_for_model(obj),
                                          object_id=str(obj.pk)).latest('created_date')
            logging.debug("Found changeset")
        except:
            if create:
                qs = ChangeSet.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                              object_id=str(obj.pk))
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
        logging.debug("STARTING QUERYSET SOFT-DELETE: %s. %s", self, len(self))
        for obj in self:
            rs, c = SoftDeleteRecord.objects.get_or_create(changeset=cs or _determine_change_set(obj),
                                                           content_type=ContentType.objects.get_for_model(obj),
                                                           object_id=str(obj.pk))
            logging.debug(" -----  CALLING delete() on %s", obj)
            obj.delete(using, *args, **kwargs)

    def undelete(self, using='default', *args, **kwargs):
        logging.debug("UNDELETING %s", self)
        for obj in self:
            cs = _determine_change_set(obj)
            cs.undelete()
        logging.debug("FINISHED UNDELETING %s", self)


class SoftDeleteManager(models.Manager):

    def _get_base_queryset(self):
        '''
        Convenience method for grabbing the base query set. Accounts for the
        deprecation of get_query_set in Django 18.
        '''

        if django.VERSION >= (1, 8, 0, 'final', 0):
            return super(SoftDeleteManager, self).get_queryset()
        else:
            return super(SoftDeleteManager, self).get_query_set()

    def _get_self_queryset(self):
        '''
        Convenience method for grabbing the query set. Accounts for the
        deprecation of get_query_set in Django 1.8
        '''

        if django.VERSION >= (1, 8, 0, 'final', 0):
            return self.get_queryset()
        else:
            return self.get_query_set()

    def get_query_set(self):
        qs = super(SoftDeleteManager, self).get_query_set().filter(
            deleted_at__isnull=True)
        if not issubclass(qs.__class__, SoftDeleteQuerySet):
            qs.__class__ = SoftDeleteQuerySet
        return qs

    def get_queryset(self):
        qs = super(SoftDeleteManager, self).get_queryset().filter(
            deleted_at__isnull=True)
        if not issubclass(qs.__class__, SoftDeleteQuerySet):
            qs.__class__ = SoftDeleteQuerySet
        return qs

    def all_with_deleted(self, prt=False):
        if hasattr(self, 'core_filters'):  # it's a RelatedManager
            qs = self._get_base_queryset().filter(**self.core_filters)
        else:
            qs = self._get_base_queryset()
        if not issubclass(qs.__class__, SoftDeleteQuerySet):
            qs.__class__ = SoftDeleteQuerySet
        return qs

    def deleted_set(self):
        qs = self._get_base_queryset().filter(deleted_at__isnull=False)
        if not issubclass(qs.__class__, SoftDeleteQuerySet):
            qs.__class__ = SoftDeleteQuerySet
        return qs

    def get(self, *args, **kwargs):
        if 'pk' in kwargs:
            return self.all_with_deleted().get(*args, **kwargs)
        else:
            return self._get_self_queryset().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        if 'pk' in kwargs:
            qs = self.all_with_deleted().filter(*args, **kwargs)
        else:
            qs = self._get_self_queryset().filter(*args, **kwargs)
        if not issubclass(qs.__class__, SoftDeleteQuerySet):
            qs.__class__ = SoftDeleteQuerySet
        return qs


class SoftDeleteObject(models.Model):
    deleted_at = models.DateTimeField(
        blank=True, null=True, default=None,
        editable=False, db_index=True
    )
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
        return self.deleted_at is not None

    def set_deleted(self, d):
        """Called via the admin interface (if user checks the "deleted" checkox)"""
        if d and not self.deleted_at:
            self.__dirty = True
            self.deleted_at = timezone.now()
        elif not d and self.deleted_at:
            self.__dirty = True
            self.deleted_at = None

    deleted = property(get_deleted, set_deleted)

    def _do_delete(self, changeset, related):
        rel = related.get_accessor_name()

        # Sometimes there is nothing to delete
        if not hasattr(self, rel):
            return

        try:
            if related.one_to_one:
                getattr(self, rel).delete(changeset=changeset)
            else:
                getattr(self, rel).all().delete(changeset=changeset)
        except:
            try:
                getattr(self, rel).all().delete()
            except:
                try:
                    getattr(self, rel).__class__.objects.all().delete(
                        changeset=changeset)
                except:
                    getattr(self, rel).__class__.objects.all().delete()

    @transaction.atomic
    def hard_delete(self, *args, **kwargs):
        super(SoftDeleteObject, self).delete(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.deleted_at:
            logging.debug("HARD DELETEING type %s, %s", type(self), self)
            try:
                cs = ChangeSet.objects.get(
                    content_type=ContentType.objects.get_for_model(self),
                    object_id=self.pk)
                cs.delete()
                super(SoftDeleteObject, self).delete(*args, **kwargs)
            except:
                try:
                    cs = kwargs.get('changeset') or _determine_change_set(self)
                    rs = SoftDeleteRecord.objects.get(
                        changeset=cs,
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
            logging.debug('SOFT DELETING type: %s, %s', type(self), self)
            cs = kwargs.get('changeset') or _determine_change_set(self)
            SoftDeleteRecord.objects.get_or_create(
                changeset=cs,
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk)
            self.deleted_at = timezone.now()
            self.save()
            all_related = [
                f for f in self._meta.get_fields()
                if (f.one_to_many or f.one_to_one)
                   and f.auto_created and not f.concrete
            ]

            for x in all_related:
                if x.on_delete.__name__ not in ['DO_NOTHING', 'SET_NULL']:
                    self._do_delete(cs, x)
                if x.on_delete.__name__ == 'SET_NULL':
                    rel = x.get_accessor_name()
                    getattr(self, rel).all().update(**{x.remote_field.name: None})
            logging.debug("FINISHED SOFT DELETING RELATED %s", self)
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
        logging.debug('FINISHED UNDELETING RELATED %s', self)

    def save(self, **kwargs):
        super(SoftDeleteObject, self).save(**kwargs)
        if self.__dirty:
            self.__dirty = False
            if not self.deleted:
                self.undelete()
            else:
                self.delete()

class ChangeSet(models.Model):
    id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )    
    created_date = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    record = GenericForeignKey('content_type', 'object_id')

    class Meta:
        index_together = [
            ("content_type", "object_id"),
        ]

    def get_content(self):
        self.record = self.content_type.model_class().objects.get(
            pk=self.object_id)
        return self.record

    def set_content(self, obj):
        self.record = obj

    def undelete(self, using='default'):
        logging.debug("CHANGESET UNDELETE: %s" % self)
        self.content._do_undelete(using)
        for related in self.soft_delete_records.all():
            related.undelete(using)
        self.delete()
        logging.debug("FINISHED CHANGESET UNDELETE: %s", self)

    def __str__(self):
        return 'Changeset: %s, %s' % (self.created_date, self.record)

    content = property(get_content, set_content)

class SoftDeleteRecord(models.Model):
    id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )    
    changeset = models.ForeignKey(
        ChangeSet,
        related_name='soft_delete_records',
        on_delete=models.CASCADE
    )
    created_date = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    record = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = (('changeset', 'content_type', 'object_id'),)
        index_together = [
            ("content_type", "object_id"),
        ]

    def get_content(self):
        self.record = self.content_type.model_class().objects.get(pk=self.object_id)
        return self.record

    def set_content(self, obj):
        self.record = obj

    def undelete(self, using='default'):
        self.content._do_undelete(using)

    def __str__(self):
        return u'SoftDeleteRecord: (%s), (%s/%s), %s' % (
            self.content,
            self.content_type,
            self.object_id,
            self.changeset.created_date)

    content = property(get_content, set_content)


def assign_permissions(user_or_group):
    for model in ['ChangeSet', 'SoftDeleteRecord']:
        ct = ContentType.objects.get(app_label="softdelete",
                                     model=model.lower())
        p, pc = Permission.objects.get_or_create(
            name="Can undelete a soft-deleted object",
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
