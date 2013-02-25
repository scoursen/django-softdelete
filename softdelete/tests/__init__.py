from django.db.models import loading, query
from django.core.management import call_command
from django.conf import settings
from softdelete.tests.test_sd import *
from softdelete.tests.test_views import *

settings.INSTALLED_APPS += ('softdelete.test_softdelete_app',)
loading.cache.loaded = False
call_command('syncdb', interactive=False, verbosity=False)



