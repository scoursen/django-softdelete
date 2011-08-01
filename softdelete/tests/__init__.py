from test_sd import *
from test_views import *

settings.INSTALLED_APPS.append('softdelete')
loading.cache.loaded = False
call_command('syncdb', interactive=False, verbosity=False)


