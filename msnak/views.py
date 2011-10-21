# coding: utf8

"""
Mediasnak Django Views

Contains the custom Django views for the Mediasnak application.
"""

from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django import http
from django.views.decorators.cache import cache_control
from django.views.decorators.http import etag
from django.views.decorators.vary import vary_on_headers
from django.db.models import F # used in Download view
from django.template import RequestContext, loader
from models import MediaFile # Database table for files
from exception import MediasnakError
import s3util, upload, listfiles, user, hashlib, delete
from os import environ

# A note on returning errors and infos:
# req.META['HTTP_REFERER'] (sic) gets you the last page the user was on
# but this is open to be modified by the user, could be blank etc. so should check it first
# then the error/info would need to be set as a global variable, and the user redirected
# alternatively, just let the user hit the back button


# Utility function for etag decorator    
def login_template_etag(request, *args, **kwargs):
    return hashlib.sha1(str(user.get_user_id()) + environ['CURRENT_VERSION_ID']).hexdigest()

@cache_control(no_cache=True, max_age=0)
def upload_form(request):
    "Produces an upload form for submitting files to S3."

    bucketname = "s3.mediasnak.com"
    user_id = user.get_user_id()

    page_parameters = upload.upload_form_parameters(bucketname, user_id)
    
    # Use render_to_response to fill out the HTML template
    return render_to_response('upload.html', page_parameters, context_instance=RequestContext(request))

def upload_success(request):
    "Handles the return process from S3 upload produced by upload_form and returns a success page to the user."
    # This view creates database entries for a file, the input is upload return values from S3
    
    user_id = user.get_user_id()
    
    # If they don't have the S3 return values, just send them to the upload page
    if not ('bucket' in request.GET and 'key' in request.GET and 'etag' in request.GET) :
        return http.HttpResponseRedirect('upload')

    if request.GET['bucket'] != 's3.mediasnak.com': # 'magic-string', could maybe put in S3utils
        error = "Apparently somehow this file was uploaded to the wrong bucket or the wrong bucket is being returned."
        return render_error(request, error)
    bucketname = request.GET['bucket']
    key = request.GET['key'] # this was created when upload page was requested
    etag = request.GET['etag'] # unused
    
    try:
        template_vars = upload.process_return_from_upload(bucketname, user_id, key, etag)
    except MediasnakError, err:
        return render_error(request, err)
    
    # Redirect to the file list page, with a success message
    info_message = "<h1>Success</h1><p>The file '{{ filename }}' ({{ mimetype }}) was uploaded under the ID '<code>{{ file_id }}</code>' on {{ upload_time }}.</p>"
    return redirect('msnak.views.list_files_page')

def download_page(request):
    "Displays a page with a link to download a file, or redirects to the download itself."
    # The friendly download link isn't necessarily part of a story, but is good functionality atleast for our use
    
    if 'fileid' not in request.GET:
        return render_error(request, "You did not specify which file to download.", 'filelist.html')
        # displays filelist upon error
    file_id = request.GET['fileid']
    
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # Essentially a 404, what else could we do with the return?
        return render_error(request, "Not Found: The file you are trying to download does not exist.", status=404)

    if file_entry.user_id != user.get_user_id():
        # Essentially a 403
        return render_error(request, "Forbidden: You are trying to access a file that you didn't upload.", status=403)
    
    key = 'u/'+file_id

    # Increment view count
    MediaFile.objects.filter(file_id=file_id).update(view_count=F("view_count")+1)
    
    # Sign a URL for the user
    url = s3util.sign_url('s3.mediasnak.com', key, expiry=60, format=s3util.URL_CUSTOM)
    
    # Redirect user to the calculated S3 download link
    return redirect(url)

def list_files_page(request):
    "Displays the page with a list of all the user's files"
        
    user_id = user.get_user_id()
    bucketname = "s3.mediasnak.com"
    
    # This might be useful, to use the same page to list files in a category, or even for searches
    # category = request.GET['category']
    
    orderby = None
    if 'sort' in request.GET:
        orderby = request.GET['sort']
    
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
            template_vars = listfiles.search_files(bucketname, user_id, search_by, search_term, orderby);
        except MediasnakError, err:
            return render_error(request, err, 'filelist.html')
        
        return render_to_response('filelist.html', template_vars, context_instance=RequestContext(request))

    template_vars = listfiles.get_user_file_list(user_id, bucketname, orderby)

    return render_to_response('filelist.html', template_vars, context_instance=RequestContext(request))


def file_details_page(request):
    "Displays the page with the detailed metadata about a file"

    #test: http://localhost:8081/file-details?fileid=file1
    
    user_id = user.get_user_id()
    bucketname = "s3.mediasnak.com"

    if 'fileid' not in request.GET:
        return render_error(request, "You did not specify which file to view the details of.", 'filelist.html')
    file_id = request.GET['fileid']
    
    editing = 'edit' in request.GET and request.GET['edit'] == "true"
    # Note: Python's "and" does short-circuit evaluation
    
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # Essentially a 404, what else could we do with the page?
        return render_error(request, 'There is no file by this ID!', status=404)
    except MediaFile.MultipleObjectsReturned:
        return render_error(request, 'There are multiple files by this ID - this shouldn\'t happen!')

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
        'download_url' : '/download?fileid='+file_entry.file_id,
        'file_name' : file_entry.filename,
        'upload_time' : file_entry.upload_time,
        'view_count' : file_entry.view_count,
        'comment' : file_entry.comment,
        'category' : file_entry.category,
        'tags' : file_entry.tags
    }
    return render_to_response('filedetails.html', template_vars, context_instance=RequestContext(request))

def delete_file(request):
    "Posting a fileid to this view permanently deletes the file from the system, including file stored on S3, and all metadata"
    
    user_id = user.get_user_id()
    bucketname = "s3.mediasnak.com"
    
    if 'fileid' not in request.POST:
        return render_error(request, 'You did not specify which file to delete.', 'filelist.html')
    file_id = request.POST['fileid']
    
    try:
        delete.delete_file(bucketname, user_id, file_id)
    except MediasnakError, err:
        return render_error(request, err, 'filelist.html')
        
    
    # should be '[filename] has been deleted'
    #return render_to_response('base.html', {'info': file_id + ' has been deleted.'})
    return redirect('msnak.views.list_files_page')

def purge_uploads(request):
    upload.purge_uploads()
    return HttpResponse(status=204) # 204 OK No Response

def render_error(request, error_str, template='base.html', status=200):
    if type(error_str) is not str:
        error_str = repr(error_str)
    t = loader.get_template(template)
    c = RequestContext(request, {'error': error_str})
    resp = HttpResponse(t.render(c))
    resp.status_code = status
    return resp
