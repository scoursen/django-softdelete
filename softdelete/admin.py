from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin
from django.db import models
from softdelete.models import *
from softdelete.forms import *
import logging

class SoftDeleteObjectAdmin(admin.ModelAdmin):
    form = SoftDeleteObjectAdminForm
    actions = ['delete_selected', 'soft_undelete']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = 'Soft delete selected objects'

    def soft_undelete(self, request, queryset):
        queryset.undelete()
    soft_undelete.short_description = 'Undelete selected objects'

    def queryset(self, request):
        try:
            qs = self.model._default_manager.all_with_deleted()
        except Exception as ex:
            qs = self.model._default_manager.all()

        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


class SoftDeleteObjectInline(admin.TabularInline):
    exclude = ('deleted_flag',)

    def change_view(self, request, object_id, extra_context=None):
        instance = self.queryset(request).get(pk=object_id)
        if instance.deleted:
            self.extra = 0
            self.max_num = 0
        super(SoftDeleteObjectInline, self).change_view(request,
                                                        object_id,
                                                        extra_context)

    def queryset(self, request):
        qs = self.model._default_manager.all_with_deleted()
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

class SoftDeleteRecordInline(admin.TabularInline):
    model = SoftDeleteRecord
    max_num = 0
    exclude = ('content_type', 'object_id',)
    readonly_fields = ('content',)

class SoftDeleteRecordAdmin(admin.ModelAdmin):
    model = SoftDeleteRecord
    form = SoftDeleteRecordAdminForm

    def change_view(self, request, object_id, extra_context=None):
        rv = super(SoftDeleteRecordAdmin, self).change_view(request,
                                                     object_id,
                                                     extra_context)
        if request.POST.has_key('undelete'):
            obj = SoftDeleteRecord.objects.get(pk=object_id)
            obj.undelete()
            return HttpResponseRedirect('../')
        return rv

    def has_delete_permission(self, *args, **kwargs):
        return False

class ChangeSetAdmin(admin.ModelAdmin):
    model = ChangeSet
    form = ChangeSetAdminForm
    inlines = (SoftDeleteRecordInline,)

    def change_view(self, request, object_id, extra_context=None):
        rv = super(ChangeSetAdmin, self).change_view(request,
                                                     object_id,
                                                     extra_context)
        if request.POST.has_key('undelete'):
            obj = ChangeSet.objects.get(pk=object_id)
            obj.undelete()
            return HttpResponseRedirect('../')
        return rv
        
    def has_delete_permission(self, *args, **kwargs):
        return False

admin.site.register(SoftDeleteRecord, SoftDeleteRecordAdmin)
admin.site.register(ChangeSet, ChangeSetAdmin)

