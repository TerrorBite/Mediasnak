from django.conf.urls.defaults import *

# On the deployed version, homedir will always be ''
import os
homedir = os.path.abspath(os.path.dirname(__file__))

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
    ('^_ah/warmup$', 'djangoappengine.views.warmup'),
    ('^$', 'django.views.generic.simple.direct_to_template', {'template': 'home.html'}),
    
    ('^upload$', 'msnak.views.upload_form', {}),
    ('^success$', 'msnak.views.upload_success', {}),

    ('^favicon.ico$', 'django.views.static.serve',
     {'path': 'favicon.ico', 'document_root' : homedir}),
    ('^icon.png$', 'django.views.static.serve',
     {'path': 'icon.png', 'document_root' : homedir}),
    ('^style.css$', 'django.views.static.serve',
     {'path': 'style.css', 'document_root' : homedir}),
)
