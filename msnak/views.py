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
from boto.s3.connection import S3Connection
import s3util

def upload_form(request):
    "Produces an upload form for submitting files to S3."

    user_id = 0 # dummy value for now until we get multiple user support

    import upload
    page_parameters = upload_form_parameters(user_id)
    
    # Use render_to_response to fill out the HTML template
    return render_to_response('upload.html', page_parameters)

def upload_success(request):
    "Handles the return process from S3 upload produced by upload_form and returns a success page to the user."
    # This view creates database entries for a file, the input is upload return values from S3

    import upload
    page_parameters = upload_return_page_parameters()
    
    # Use render_to_response shortcut to fill out the HTML template
    return render_to_response('upload-success.html', template_vars)

def download_page(request):
    "Displays a page with a link to download a file, or redirects to the download itself."
    # The friendly download link isn't necessarily part of a story, but is good functionality atleast for our use
    
    # If they don't have the S3 return values, just send them to the upload page
    if not ('bucket' in request.GET and 'key' in request.GET and 'etag' in request.GET) :
        return http.HttpResponseRedirect('upload')
        
    import download
    
    
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

    #delete file off database
    try:
        MediaFile.delete()
    except NotSavedError:
        return render_to_response('base.html',{'error':'The file does not exist.'})

    #delete the file off S3
    botoconn = S3Connection(access_keys.key_id, access_keys.secret)
    bucket = botoconn.create_bucket(bucketname)
    bucket.delete_key(key_name)
    
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

    #expand this as we add extra fields (eg. author etc)
    if search_by == "default":
        for item in file_entries:
            #neaten this up later
            if (search_term in item.filename) or (search_term in item.file_id):
                results.append(
                    {
                    'file_id' : item.file_id, # can be used in a URL to access the information page for this file
                    'download_url' : s3util.sign_url(bucketname, item.file_id),
                    'name' : item.filename,
                    'upload_time' : item.upload_time,
                    'view_count' : item.view_count
                    }
                )
    else if search_by == "filename":
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
        return render_to_response('base.html',{'info':'No search results returned'})
    else:
        template_vars = {
            'file_list_entries': results
        }
        return render_to_response('filelist.html', template_vars)
