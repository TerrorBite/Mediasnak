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

    # Static files
    ('^favicon.ico$', 'django.views.generic.simple.redirect_to',
        {'url': 'http://s3.mediasnak.com/assets/favicon.ico', 'permanent' : True}),
    ('^robots.txt$', 'django.views.static.serve',
     {'path': 'static/robots.txt', 'document_root' : homedir}),
    ('^style.css$', 'django.views.static.serve',
     {'path': 'static/style.css', 'document_root' : homedir}),

    # Development
    ('^test-databases$', 'msnak.dev_views.test_databases', {}),
    ('^view-mediafile-table$', 'msnak.dev_views.view_mediafile_model', {}),
    ('^filenametest$', 'msnak.dev_views.show_filename', {}),
)
