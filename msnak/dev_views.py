import access_keys
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from random import randrange
from base64 import urlsafe_b64encode, b64encode
from datetime import datetime, timedelta
from msnak.s3util import hmac_sign
from models import MediaFile # Database table for files


def test_databases(request):

    set = request.GET['set']
    if set == 'true':
        f = MediaFile(file_id='testfileid', user_id=1, filename='testfilename',
        upload_time=datetime.utcnow(), view_count=0)#time.ctime #datetime.datetime
        f.save()
    
    retr = MediaFile.objects.all()[0]
    
    file_id = retr.file_id
    user_id = retr.user_id
    filename = retr.filename
    upload_time = retr.upload_time
    view_count = retr.view_count
    
    return render_to_response('test-databases.html', {'file_id':file_id,'user_id':user_id,'filename':filename,'upload_time':upload_time,'view_count':view_count})

def view_mediafile_model(request):

    retr = MediaFile.objects.all()
    
    # Could filter with the request's GET input

    
    # Multiple html repeats could be done with a template but I don't feel like
    # learning that at the moment
    content = '<html><head><title>MediaFile Table</title></head><body>';
    for r in retr:
      content += '''
        <div><pre>
        file_id------ '''+str(r.file_id)+'''
        user_id------ '''+str(r.user_id)+'''
        filename----- '''+str(r.filename)+'''
        upload_time-- '''+str(r.upload_time)+'''
        view_count--- '''+str(r.view_count)+'''
        </pre></div>
        '''
    content += '</body>'
    
    return HttpResponse(content)
    
def load_test_database_data(request):

    # The following lets us call django-admin.py (manage.py) commands from python
    from django.core.management import call_command
    # Equivalent to running 'manage.py loaddata'
    call_command('loaddata', 'msnak_testfixture.json')

    return HttpResponse("Data (may have been) Loaded<br><a href='view-mediafile-table'>/view-mediafile-table</a>")

def show_filename(request):

    key = request.GET['key']

    from boto.s3.connection import S3Connection

    # The keys can be set as environment variables instead
    botoconn = S3Connection(access_keys.key_id, access_keys.secret)
    bucket = botoconn.create_bucket('s3.mediasnak.com')

    file = bucket.get_key(key)
    if file is None:
        return render_to_response('base.html', { 'error': 'This file key is invalid!' })

    filename = file.get_metadata('filename')
    if filename is None:
        return render_to_response('base.html', { 'error': 'There was an error, the remote metadata on this file couldn\'t be found' })

    content = 'key - ' + key + '<br> filename - ' + filename

    return HttpResponse(content)