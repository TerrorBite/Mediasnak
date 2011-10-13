# coding: utf8

"""
Mediasnak Django Views

Contains the custom Django views for the Mediasnak application.
"""

from django.http import HttpResponse
# A little trickery follows: render_to_response is imported with an altered name
# as we now provide a "fake" render_to_response that adds some stuff we need.
from django.shortcuts import render_to_response as real_render_to_response
from django import http
from boto.s3.connection import S3Connection
from models import MediaFile # Database table for files
import s3util, accounts, exception, upload, listfiles, user
from google.appengine.api import users

# A note on returning errors and infos:
# req.META['HTTP_REFERER'] (sic) gets you the last page the user was on
# but this is open to be modified by the user, could be blank etc. so should check it first
# then the error/info would need to be set as a global variable, and the user redirected
# alternatively, just let the user hit the back button




def upload_form(request):
    "Produces an upload form for submitting files to S3."

    bucketname = "s3.mediasnak.com"
    user_id = accounts.get_logged_in_user()

    page_parameters = upload.upload_form_parameters(bucketname, user_id)
    
    # Use render_to_response to fill out the HTML template
    return render_to_response('upload.html', page_parameters)

def upload_success(request):
    "Handles the return process from S3 upload produced by upload_form and returns a success page to the user."
    # This view creates database entries for a file, the input is upload return values from S3
    
    user_id = accounts.get_logged_in_user()
    
    # If they don't have the S3 return values, just send them to the upload page
    if not ('bucket' in request.GET and 'key' in request.GET and 'etag' in request.GET) :
        return http.HttpResponseRedirect('upload')

    if request.GET['bucket'] != 's3.mediasnak.com': # 'magic-string', could maybe put in S3utils
        error = "Apparently somehow this file was uploaded to the wrong bucket or the wrong bucket is being returned."
        return render_to_response('base.html', { 'error': error })
    bucketname = request.GET['bucket']
    key = request.GET['key'] # this was created when upload page was requested
    etag = request.GET['etag'] # unused
    
    try:
        template_vars = upload.process_return_from_upload(bucketname, user_id, key, etag)
    except MediasnakError, err:
        return render_to_response('base.html', { 'error': str(err) })
    
    template_vars.update({ 'bucket': bucketname, 'key': key, 'etag': etag,
                           'file_id': key, 'user_id': user_id })
    
    # Use render_to_response shortcut to fill out the HTML template
    return render_to_response('upload-success.html', template_vars)

def download_page(request):
    "Displays a page with a link to download a file, or redirects to the download itself."
    # The friendly download link isn't necessarily part of a story, but is good functionality atleast for our use
    
    if 'filename' not in request.GET:
        return render_to_response('download.html', { 'error': 'error, no filename specified' })
        # redirect to homepage or something
    filename = request.GET['filename']
    
    try:
        file_entry = MediaFile.objects.get(filename=filename)
    except MediaFile.DoesNotExist:
        # Essentially a 404, what else could we do with the return?
        return render_to_response('base.html', { 'error': "There seems to have been no file by this name." })
    except MediaFile.MultipleObjectsReturned:
        pass
    
    key = file_entry.file_id
    
    url = s3util.sign_url(bucketname, key)
    
    # Use render_to_response shortcut to fill out the HTML template
    return render_to_response('download.html', { 'url': url })

def list_files_page(request):
    "Displays the page with a list of all the user's files"
        
    user_id = accounts.get_logged_in_user()
    bucketname = "s3.mediasnak.com"
    
    # This might be useful, to use the same page to list files in a category, or even for searches
    # category = request.GET['category']
    
    #def search_files(request):
    #"displays a list of files matching the request"
    if 'searchterm' in request.GET:
        #.. return render_to_response('base.html',{'error':'No serch term specified'});
        search_term = request.GET['searchterm']
        
        if 'searchby' in request.GET:
            search_by = request.GET['searchby']
        else:
            search_by = 'default'
            #.. return render_to_response('base.html',{'error':'Nothing specified to search by.'})
        
        try:
            template_vars = listfiles.search_files(bucketname, user_id, search_by, search_term);
        except MediasnakError, err:
            return render_to_response('filelist.html', { 'error': str(err) })
        
        #template_vars= {'info':'test'}
        return _render_with_login('filelist.html', template_vars)

    template_vars = listfiles.get_user_file_list(user_id, bucketname)

    return render_to_response('filelist.html', template_vars)


def file_details_page(request):
    "Displays the page with the detailed metadata about a file"

    #test: http://localhost:8081/file-details?fileid=file1
    
    user_id = accounts.get_logged_in_user()
    bucketname = "s3.mediasnak.com"

    if 'fileid' not in request.GET:
        return render_to_response('filelist.html', {'error': 'No fileid was included. Please choose a file.'})
    file_id = request.GET['fileid']
    
    editing = 'edit' in request.GET and request.GET['edit'] == "true"
    # Note: Python's "and" does short-circuit evaluation
    
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # Essentially a 404, what else could we do with the page?
        return render_to_response('base.html', { 'error': 'There seems to have been no file by this fileid!' })
    except MediaFile.MultipleObjectsReturned:
        return render_to_response('base.html', { 'error': 'There seems to be multiple files by this fileid!' })

    # Process edits to details if they have been submitted
    
    # These user input fields need checking
    #### WHAT ARE THE DATABASE INJECTION RISKS OF DJANGO ?? ####
    
    # submitting the following complex string as a filename does not work as expected
    # <QueryDict: {u'fileviewcount': [u'100'], u'submit': [u'Submit Edits'], u'filename': [u'<QueryDict: {u\'fileviewcount\': [u\'100\'],
    # u\'submit\': [u\'Submit Edits\'], u\'filename\': [u\'<QueryDict: {u\\\'fileviewcount\\\': [u\\\'100\\\'], u\\\'submit\\\':
    # [u\\\'Submit Edits\\\'], u\\\'filename\\\': [u\\\'<QueryDict: {u\\\\\\\'fileviewcount\\\\\\\': [u\\\\\\\'100\\\\\\\'], u\\\\\\\
    #'filename\\\\\\\': [u"<QueryDict: {u\\\\\\\'
    #fileviewcount\\\\\\\': [u\\\\\\\'100\\\\\\\'], u\\\\\\\'filename\\\\\\\': [u\\\\\\\'<QueryDict: {}>\\\\\\\']}>"]}>\\\']}>\']}>']}>
    
    # does not check lengths for instance
    #also, how does django display values (does it encode html special characters?)
    
    if 'submit' in request.POST and request.POST['submit'] == 'Submit Edits':
        if 'filename' in request.POST:
            file_entry.filename = request.POST['filename']
        if 'fileviewcount' in request.POST:
            file_entry.view_count = request.POST['fileviewcount']
        if 'filecomment' in request.POST:
            file_entry.comment = request.POST['filecomment']
        if 'filecategory' in request.POST:
            file_entry.category = request.POST['filecategory']
        if 'filetags' in request.POST:
            file_entry.tags = request.POST['filetags']
        file_entry.save()
        editing = False;
        
        
    template_vars = {
        'editing' : editing,
        'file_id' : file_entry.file_id,
        'download_url' : s3util.sign_url(bucketname, file_entry.file_id),
        'file_name' : file_entry.filename,
        'upload_time' : file_entry.upload_time,
        'view_count' : file_entry.view_count,
        'comment' : file_entry.comment,
        'category' : file_entry.category,
        'tags' : file_entry.tags
    }
    return render_to_response('filedetails.html', template_vars)

def delete_file(request):
    "Posting a fileid to this view permanently deletes the file from the system, including file stored on S3, and all metadata"
    
    user_id = accounts.get_logged_in_user()
    bucketname = "s3.mediasnak.com"
    
    if 'fileid' not in request.POST:
        return render_to_response('filelist.html', {'error': 'No fileid was specified. Please choose a file'})
    file_id = request.POST['fileid']
    
    try:
        delete.delete_file(bucketname, user_id, file_id)
    except MediasnakError, err:
        return render_to_response('filelist.html', { 'error': str(err) })
    
    # should be '[filename] has been deleted'
    return render_to_response('base.html', {'info': file_id + ' has been deleted.'})

def template_with_login(request, template):
	"Simple direct-render view that correctly sets vars to display a login or logout link."
	return real_render_to_response(template, user.template_vars())

def render_to_response(template, vars={}, *args, **kwargs):
	"A render_to_response replacement that auto-fills required variables."
	return real_render_to_response(template, user.template_vars(vars), *args, **kwargs)
	