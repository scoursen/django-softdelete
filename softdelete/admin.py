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

    def queryset(self, request):
        qs = self.model._default_manager.all_with_deleted()
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def clean(self):
        logging.info("SoftDeleteObjectInline.clean")
        return super(SoftDeleteObjectInline, self).clean()

class SoftDeleteRecordInline(admin.TabularInline):
    model = SoftDeleteRecord
    exclude = ('content_type', 'object_id',)
    readonly_fields = ('content',)

class ChangeSetAdmin(admin.ModelAdmin):
    model = ChangeSet
    inlines = (SoftDeleteRecordInline,)

admin.site.register(SoftDeleteRecord)
admin.site.register(ChangeSet, ChangeSetAdmin)

