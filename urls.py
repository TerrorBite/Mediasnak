from django.conf.urls.defaults import *

# On the deployed version, homedir will always be ''
import os
homedir = os.path.abspath(os.path.dirname(__file__))

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
    ('^_ah/warmup$', 'djangoappengine.views.warmup'),
    ('^$', 'django.views.generic.simple.direct_to_template',
     {'template': 'home.html'}),
     
    ('^upload$', 'views.upload_form',
     {}),
    ('^favicon.ico$', 'django.views.static.serve',
     {'path': 'favicon.ico', 'document_root' : homedir}),
)
