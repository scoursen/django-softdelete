from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import admin
from django.db import models
from softdelete.models import *
from softdelete.admin.forms import *
import logging


class SoftDeleteObjectInline(admin.TabularInline):
    class Meta:
        exclude = ('deleted_at',)

    def __init__(self, parent, site, *args, **kwargs):
        super(SoftDeleteObjectInline, self).__init__(parent, site, *args, **kwargs)
        if parent.deleted:
            self.extra = 0
            self.max_num = 0

    def get_queryset(self, request):
        qs = self.model._default_manager.all_with_deleted()
        ordering = self.get_ordering(request) or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    queryset = get_queryset


class SoftDeleteObjectAdmin(admin.ModelAdmin):
    form = SoftDeleteObjectAdminForm
    actions = ['delete_selected', 'soft_undelete', 'hard_delete']

    def delete_selected(self, request, queryset):
        queryset.delete()

    delete_selected.short_description = 'Soft delete selected objects'

    def soft_undelete(self, request, queryset):
        queryset.undelete()

    soft_undelete.short_description = 'Undelete selected objects'

    def hard_delete(self, request, queryset):
        for obj in queryset:
            if obj.deleted_at:
                obj.delete()
            else:
                obj.hard_delete()
    hard_delete.short_description = 'Hard delete selected objects'

    def response_change(self, request, obj, *args, **kwargs):
        if 'undelete' in request.POST:
            return HttpResponseRedirect('../')
        return super(SoftDeleteObjectAdmin, self).response_change(request, obj, *args, **kwargs)

    def get_queryset(self, request):
        try:
            qs = self.model._default_manager.all_with_deleted()
        except Exception as ex:
            qs = self.model._default_manager.all()

        ordering = self.get_ordering(request) or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    queryset = get_queryset


class SoftDeleteRecordInline(admin.TabularInline):
    model = SoftDeleteRecord
    max_num = 0
    exclude = ('content_type', 'object_id',)
    readonly_fields = ('content',)


class SoftDeleteRecordAdmin(admin.ModelAdmin):
    model = SoftDeleteRecord
    form = SoftDeleteRecordAdminForm
    actions = ['soft_undelete']

    def soft_undelete(self, request, queryset):
        [x.undelete() for x in queryset.all()]

    soft_undelete.short_description = 'Undelete selected objects'

    def response_change(self, request, obj, *args, **kwargs):
        if 'undelete' in request.POST:
            obj.undelete()
            return HttpResponseRedirect('../../')
        return super(SoftDeleteRecordAdmin, self).response_change(request, obj,
                                                                  *args, **kwargs)

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class ChangeSetAdmin(admin.ModelAdmin):
    model = ChangeSet
    form = ChangeSetAdminForm
    inlines = (SoftDeleteRecordInline,)
    actions = ['soft_undelete']

    def soft_undelete(self, request, queryset):
        [x.undelete() for x in queryset.all()]

    soft_undelete.short_description = 'Undelete selected objects'

    def response_change(self, request, obj, *args, **kwargs):
        if 'undelete' in request.POST:
            obj.undelete()
            return HttpResponseRedirect('../../')
        return super(ChangeSetAdmin, self).response_change(request, obj,
                                                           *args, **kwargs)

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


admin.site.register(SoftDeleteRecord, SoftDeleteRecordAdmin)
admin.site.register(ChangeSet, ChangeSetAdmin)
