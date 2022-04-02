import sys
import os
import django

BASE_DIR = os.path.dirname(__file__)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'my_db',
        }
    }

INSTALLED_APPS = [
    'softdelete',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
]

if django.VERSION[0] >= 2:
    MIDDLEWARE = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]
    SILENCED_SYSTEM_CHECKS = (
        'admin.E130',
    )
else:
    MIDDLEWARE_CLASSES= [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'tests/templates')
        ],
        'OPTIONS': {
             'debug': True,
             'loaders': (
                  'django.template.loaders.filesystem.Loader',
                  'django.template.loaders.app_directories.Loader',
              ),
             'context_processors': (
                 'django.contrib.messages.context_processors.messages',
                 'django.contrib.auth.context_processors.auth',
                 'django.template.context_processors.request'
             )
         }
    },
]


DOMAIN = 'http://testserver'
ROOT_URLCONF = 'softdelete.urls'
SECRET_KEY = "dummy"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if 'test' in sys.argv:
    INSTALLED_APPS.append("softdelete.test_softdelete_app")
