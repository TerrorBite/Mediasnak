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
    ('^download$', 'msnak.views.download_page', {}),
	('^delete$', 'msnak.views.delete_file', {}),
    
    ('^files$', 'msnak.views.list_files_page', {}),
    ('^file-details$', 'msnak.views.file_details_page', {}),
    
    ('^fileinfo$', 'django.views.generic.simple.direct_to_template', {'template': 'fileinfo.html'}),

    # Static files
    ('^favicon.ico$', 'django.views.generic.simple.redirect_to',
        {'url': 'http://s3.mediasnak.com/assets/favicon.ico', 'permanent' : True}),
    ('^icon.png$', 'django.views.generic.simple.redirect_to',
        {'url': 'http://s3.mediasnak.com/assets/icon.png', 'permanent' : True}),
    ('^robots.txt$', 'django.views.static.serve',
     {'path': 'msnak/static/robots.txt', 'document_root' : homedir}),
    ('^static/style.css$', 'django.views.static.serve',
     {'path': 'msnak/static/style.css', 'document_root' : homedir}),

    # Development
    (r'^test', include('gaeunit.urls')),
    #('^databasetest$', 'msnak.dev_views.test_databases', {}),
    ('^viewdatabase$', 'msnak.dev_views.view_mediafile_model', {}),
    ('^loaddatabase$', 'msnak.dev_views.load_test_database_data', {}),
    #('^filenametest$', 'msnak.dev_views.show_filename', {}),
)
