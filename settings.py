# Initialize App Engine and import the default settings (DB backend, etc.).
# If you want to use a different backend you have to remove all occurences
# of "djangoappengine" from this file.
from djangoappengine.settings_base import *

import os
import access_keys

# Activate django-dbindexer for the default database
DATABASES['native'] = DATABASES['default']
DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
AUTOLOAD_SITECONF = 'indexes'

SECRET_KEY = access_keys.secret

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'djangotoolbox',
    'autoload',
    'dbindexer',
    'msnak',

    # djangoappengine should come last, so it can override a few manage.py commands
    'djangoappengine',
)

MIDDLEWARE_CLASSES = (
    # This loads the index definitions, so it has to come first
    'autoload.middleware.AutoloadMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'msnak.user.template_vars', # Insert the username and login/logout vars into templates
)

# This test runner captures stdout and associates tracebacks with their
# corresponding output. Helps a lot with print-debugging.
TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

ADMIN_MEDIA_PREFIX = '/media/admin/'
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'msnak/templates'),) # when msnak is registered as an INSTALLED_APPS above, this is unnecessary
FIXTURE_DIRS = ('/msnak/fixtures/',) # when msnak is registered as an INSTALLED_APPS above, this is unnecessary
ROOT_URLCONF = 'urls'
