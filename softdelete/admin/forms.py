from django.forms import *
from softdelete.models import *
from softdelete.forms import *
import logging

class SoftDeleteObjectAdminForm(ModelForm):
    deleted = BooleanField(required=False)
    
    class Meta:
        model = SoftDeleteObject
        exclude = ('deleted_at',)

    def __init__(self, *args, **kwargs):
        super(SoftDeleteObjectAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.initial['deleted'] = instance.deleted

    def clean(self, *args, **kwargs):
        cleaned_data = super(SoftDeleteObjectAdminForm, self).clean(*args, **kwargs)
        if 'undelete' in self.data:
            self.instance.deleted = False
            cleaned_data['deleted'] = False
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        model = super(SoftDeleteObjectAdminForm, self).save(commit=False, 
                                                            *args, **kwargs)
        model.deleted = self.cleaned_data['deleted']
        if commit:
            model.save()
        return model

class ChangeSetAdminForm(ChangeSetForm):
    pass

class SoftDeleteRecordAdminForm(ModelForm):
    class Meta:
        model = SoftDeleteRecord
        readonly_fields = ('created', )
        exclude = ('content_type', 'object_id', 'changeset')

