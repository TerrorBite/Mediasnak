# coding: utf8

"""
Mediasnak Django Views

Contains the custom Django views for the Mediasnak application.
"""

import access_keys
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from random import randrange
from base64 import urlsafe_b64encode, b64encode
from datetime import datetime, timedelta
from msnak.s3util import hmac_sign
from models import MediaFile # Database table for files
from django import http
import s3util

def upload_form(request):
    "Produces an upload form for submitting files to S3."

    user_id = 0 # dummy value for now until we get multiple user support

    # You know how Youtube has those video IDs that look like "r_xHTXf-iIY"?
    # This line randomly generates one of those (it's just an 8 bit random value).
    uniq = urlsafe_b64encode(''.join([chr(randrange(255)) for x in xrange(8)]))[:11]

    # Put together a key
    key = 'u/%s' % (uniq,)

    # Expiry date string in ISO8601 GMT format, one hour in the future:
    expiry = (datetime.utcnow() + timedelta(hours=1)).isoformat()+'Z'

    # Construct policy string from JSON. This ensures that if the user tries something sneaky such as
    # altering the hidden form fields, then the upload will be rejected.
    policy_str = simplejson.dumps({
        'expiration': expiry,
        'conditions': [
            {'key': key},
            {'acl': 'private'},
            {'bucket': 's3.mediasnak.com'},
            ['starts-with', '$Content-Disposition', 'inline; filename='],
            ['starts-with', '$Content-Type', ''],
            {'success_action_redirect': 'http://www.mediasnak.com/success'},
	    ['starts-with', '$x-amz-meta-filename', '']
            ]
        })

    policy = b64encode(policy_str.encode('utf8'))
    signature = hmac_sign(policy)

    # Use render_to_response to fill out the HTML template
    return render_to_response('upload.html', {'key': key, 'aws_id': access_keys.key_id, 'policy': policy, 'signature': signature})

def upload_success(request):
    "Handles the return process from S3 upload produced by upload_form and returns a success page to the user."
    # This view creates database entries for a file, the input is upload return values from S3

    error = '' # this will hold an error message if we need one to put in the template

    # If they don't have the S3 return values, just send them to the upload page
    if not ('bucket' in request.GET and 'key' in request.GET and 'etag' in request.GET) :
        return http.HttpResponseRedirect('upload')

    bucketname = request.GET['bucket']
    if bucketname != 's3.mediasnak.com': # 'magic-string', could maybe put in S3utils
        error = "Apparently somehow this file was uploaded to the wrong bucket or the wrong bucket is being returned."
        return render_to_response('base.html', { 'error': error })
    key = request.GET['key'] # this was created when upload page was requested
    etag = request.GET['etag'] # unused
    file_id = key

    # get logged-in user
    user_id = 0
    
    # Save the key in the database, so that we can match it up when the upload is finished
    # and also ensure it was a valid upload
    # The filename, upload time and view count will be filled in later (just setting upload time to the current time for now)
    # User ID may also be checked later
    file_entry = MediaFile(file_id=key, user_id=user_id, filename='', upload_time=datetime.utcnow(), view_count=0)
    file_entry.save()

    # check database that this matches a valid upload
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # if the entry hasn't been created yet ...
        # What to do now?
        # Either user could re-upload the file,
        # or the system could simply create the file_id now instead assuming there's no reason not to
        template_vars = {
            'error': "There seems to have been no file set-up for this upload."
        }
        return render_to_response('base.html', template_vars)
    except MediaFile.MultipleObjectsReturned:
        ## this error will be reached if the user goes back and tries to upload again ##
        # means a file may be overridden in s3
        template_vars = {
            'error': "Apparently this file's ID has already finished uploading before.",
            'bucket': bucketname, 'key': key, 'etag': etag,
            'file_id': file_id, 'user_id': user_id
        }
        return render_to_response('upload-success.html', template_vars)

    # could check the file upload belongs to this user
    if file_entry.user_id != user_id:
        return render_to_response('base.html',{'error': "Apparently this file upload wasn't requested by the logged-in user."}

    # Make sure this file-id hasn't been already used for another file somehow?
    # for instance, if the user reloads the page, the file information will be overridden

    # extract filename from s3
    # ..use key, or etag?
    key = request.GET['key']
    filename = s3util.get_metadata_from_s3(bucketname, key, 'filename')

    # check that this etag matches this key?    
    
    upload_time = datetime.utcnow()

    # Set the file status as uploaded in database
    file_entry.filename=filename
    file_entry.upload_time=upload_time
    file_entry.save()
    # Now everything for the file entry except view_count should now be filled in

    # Get the information for this file (which was just saved)
    # file_entry = MediaFile.objects.get(file_id=file_id)
    
    #url = s3util.sign_url(bucket, key)
    # strange there's no way to get the bucket name from a bucket object
    # also, is it sent back by Amazon?
    # we need to make a global for this magic-value
    url = s3util.sign_url(bucketname, key)
    
    # Use render_to_response shortcut to fill out the HTML template
    template_vars = {
        'url': url,
        'bucket': bucketname, 'key': key, 'etag': etag,
        'upload_time': upload_time, 'file_id': file_id, 'user_id': user_id, 'filename': filename
    }
    return render_to_response('upload-success.html', template_vars)

def download_page(request):
    "Displays a page with a link to download a file, or redirects to the download itself."
    # The friendly download link isn't necessarily part of a story, but is good functionality atleast for our use
    
    #if 'page' in request.GET:
    #    if request.GET['page'] == True:
    #        # then don't redirect, else redirect
    #        pass
    
    bucketname = 's3.mediasnak.com'
    
    if 'filename' not in request.GET:
        return render_to_response('download.html', { 'error': 'error, no filename specified' })
        # redirect to homepage or something
    filename = request.GET['filename']
    
    try:
        file_entry = MediaFile.objects.get(filename=filename)
    except MediaFile.DoesNotExist:
        error = "<p>There seems to have been no file by this name.</p>"
        # Essentially a 404, what else could we do with the return?
        return render_to_response('base.html', { 'error': error })
    except MediaFile.MultipleObjectsReturned:
        pass
    
    key = file_entry.file_id
    
    import s3util
    url = s3util.sign_url(bucketname, key)
    
    # Use render_to_response shortcut to fill out the HTML template
    return render_to_response('download.html', { 'url': url })

def list_files_page(request):
    "Displays the page with a list of all the user's files"

    # This might be useful, to use the same page to list files in a category, or even for searches
    # category = request.GET['category']

    user_id = 0
    bucketname = "s3.mediasnak.com"

    file_entries = MediaFile.objects.filter(user_id=user_id) # what exceptions might this raise?
    
    # file_list_entries is the file information which will be used by the template
    file_list_entries = []
    filenames = []
    for file in file_entries:
        # possible search implementation can be added here:
        # if file_matches_search(file, search) or 'search' not in request.GET:
        file_list_entries.append(
            {
            'file_id' : file.file_id, # can be used in a URL to access the information page for this file
            'download_url' : s3util.sign_url(bucketname, file.file_id),
            'name' : file.filename,
            'upload_time' : file.upload_time,
            'view_count' : file.view_count
            }
        )
        # alternative dictionary syntax, apparently
        # dict(
        # file_id = file.file_id, # can be used in a URL to access the information page for this file
        # download_url = s3util.sign_url(bucketname, file.file_id),
        # name = file.filename,
        # upload_time = file.upload_time,
        # view_count = file.view_count
        # )
    
    # Use render_to_response shortcut to fill out the HTML template
    template_vars = {
        'file_list_entries': file_list_entries
    }
    return render_to_response('filelist.html', template_vars)


def file_details_page(request):
    "Displays the page with the detailed metadata about a file"

    #test: http://localhost:8081/file-details?fileid=file1

    user_id = 0
    bucketname = "s3.mediasnak.com"

    if 'fileid' not in request.GET:
        return render_to_response('base.html', {'error': 'Please specify a fileid!'}) # this could instead give the user a choice of files

    file_id = request.GET['fileid']

    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # Essentially a 404, what else could we do with the return?
        return render_to_response('base.html', { 'error': 'There seems to have been no file by this fileid!' })
    except MediaFile.MultipleObjectsReturned:
        return render_to_response('base.html', { 'error': 'There seems to be multiple files by this fileid!' })

    # Use render_to_response shortcut to fill out the HTML template
    template_vars = {
        'file_id' : file_entry.file_id, # can be used in a URL to access the information page for this file
        'download_url' : s3util.sign_url(bucketname, file_entry.file_id),
        'file_name' : file_entry.filename,
        'upload_time' : file_entry.upload_time,
        'view_count' : file_entry.view_count
    }
    return render_to_response('filedetails.html', template_vars)

    
def delete_file(request):
    "Posting a fileid to this view permanently deletes the file from the system, including file stored on S3, and all metadata"
    user_id = 0
    bucketname = "s3.mediasnak.com"
    
    if 'fileid' not in request.GET:
        return render_to_response('base.html', {'error': 'No fileid was specified.'})

    file_id = request.GET['fileid']

    #check that the file actually exists
##    try:
##        MediaFile.objects.get(filename=filename)
##    except MediaFile.DoesNotExist:
##        error = "<h3>There was an error:</h3>" + \
##                "<p>There seems to have been no file by this name.</p>"
##        # Essentially a 404, what else could we do with the return?
##        return render_to_response('base.html', { 'error': error })
##    except MediaFile.MultipleObjectsReturned:
##        pass

    #delete the file off S3
        #how?
    
    #delete file off database
    try:
        MediaFile.delete()
    except NotSavedError:
        return render_to_response('base.html',{'error':'The file does not exist.'})
        
    #done!
    return render_to_response('base.html',{'info':'The file was deleted!'})


#added by kieran, probably not called by anything yet
def search_files(request):
    "displays a list of files matching the request"

    if 'searchterm' not in request.GET:
        return render_to_response('base.html',{'error':'No serch term specified'});

    if 'searchby' not in request.GET:
        return render_to_response('base.html',{'error':'Nothing specified to search by.'})

    search_by = request.GET['searchby']
    search_term = request.GET['searchterm']

    user_id = 0
    bucketname = "s3.mediasnak.com"
    file_entries = MediaFile.objects.filter(user_id=user_id)
    results = []

    if search_by == "filename":
        for item in file_entries:
            if search_term in item.filename:
                results.append(
                    {
                    'file_id' : item.file_id, # can be used in a URL to access the information page for this file
                    'download_url' : s3util.sign_url(bucketname, item.file_id),
                    'name' : item.filename,
                    'upload_time' : item.upload_time,
                    'view_count' : item.view_count
                    }
                )
    else:
        return render_to_response('base.html',{'error':'That is an invalid category to search by'})

    if len(results) < 1:
        return render_to_response('base.html',{'error':'No search results returned'})
    else:
        template_vars = {
            'file_list_entries': results
        }
        return render_to_response('filelist.html', template_vars)
