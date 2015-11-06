from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.core import serializers
from django.contrib import auth
from django.contrib.auth.decorators import permission_required
from django.forms.models import inlineformset_factory
from django.views.generic import *
from django.views.generic.base import TemplateResponseMixin, View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template import RequestContext
from softdelete.forms import *
from softdelete.models import *
import logging

class ProtectedView(object):
    @method_decorator(permission_required('softdelete.can_undelete'))
    def dispatch(self, *args, **kwargs):
        return super(ProtectedView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProtectedView, self).get_context_data(**kwargs)
        context['request'] = self.request
        return context

class ChangeSetList(ProtectedView, ListView):
    model = ChangeSet

    def get_query_set(self):
        return model.objects.all()

    def get_queryset(self):
        return model.objects.all()

class ChangeSetDetail(ProtectedView, DetailView):
    model = ChangeSet

    def get_object(self):
        return get_object_or_404(ChangeSet, pk=self.kwargs['changeset_pk'])

class ChangeSetUpdate(ProtectedView, UpdateView):
    model = ChangeSet
    form_class = ChangeSetForm

    def get_object(self):
        return get_object_or_404(ChangeSet, pk=self.kwargs['changeset_pk'])

    def get_success_url(self):
        return reverse('softdelete.changeset.list')

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ChangeSetUpdate, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'Undelete':
            return HttpResponseRedirect(reverse('softdelete.changeset.view',
                                                args=(kwargs['changeset_pk'],)))
        self.get_object().undelete()
        return HttpResponseRedirect(self.get_success_url())
