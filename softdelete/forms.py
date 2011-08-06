from django.forms import *
from softdelete.models import *
import logging

class ChangeSetForm(ModelForm):
    class Meta:
        model = ChangeSet
        exclude = ('content_type', 'object_id',)

class SoftDeleteObjectAdminForm(ModelForm):
    deleted = BooleanField(required=False)
    
    class Meta:
        model = SoftDeleteObject
        exclude = ('deleted_flag',)

    def __init__(self, *args, **kwargs):
        super(SoftDeleteObjectAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.initial['deleted'] = instance.deleted_flag

    def save(self, commit=True, *args, **kwargs):
        model = super(SoftDeleteObjectAdminForm, self).save(commit=False, *args, **kwargs)
        model.deleted = self.cleaned_data['deleted']
        if commit:
            model.save()
        return model
