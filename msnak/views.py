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

    # Use render_to_response to fill out the upload.html template
    return render_to_response('upload.html', {'key': key, 'aws_id': access_keys.key_id, 'policy': policy, 'signature': signature})

def upload_success(request):
    "Handles the return process from S3 upload produced by upload_form and returns a success page to the user."

    error = '' # this will hold an error message if we need one to put in the template

    # If they don't have the S3 return values, just send them to the upload page
    if not ('bucket' in request.GET and 'key' in request.GET and 'etag' in request.GET) :
        return http.HttpResponseRedirect('upload')

    bucket = request.GET['bucket'] # unused, could check that it is equal to s3.mediasnak.com
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
        error = "<h3>There was an error:</h3>" + \
                "<p>There seems to have been no file set-up for this upload.</p>"
        # What to do now?
        # Either user could re-upload the file,
        # or the system could simply create the file_id now instead assuming there's no reason not to
        template_vars = {
            'error': error
        }
        return render_to_response('base.html', template_vars)
    except MediaFile.MultipleObjectsReturned:
        error = "<h3>There was an error:</h3>" + \
                "<p>Apparently this file's ID has already finished uploading before.</p>"
        template_vars = {
            'error': error,
            'bucket': bucket, 'key': key, 'etag': etag,
            'file_id': file_id, 'user_id': user_id
        }
        return render_to_response('upload-success.html', template_vars)

    # could check the file upload belongs to this user
    if file_entry.user_id != user_id:
        error = "<h3>There was an error:</h3>" + \
                "<p>Apparently this file upload wasn't requested by the logged-in user.</p>"

    # Make sure this file-id hasn't been already used for another file somehow?
    # for instance, if the user reloads the page, the file information will be overridden

    # extract filename from s3
    # ..use key, or etag?
    key = request.GET['key']
    #
    from boto.s3.connection import S3Connection
    #
    # The keys can be set as environment variables instead
    botoconn = S3Connection(access_keys.key_id, access_keys.secret)
    bucket = botoconn.create_bucket('s3.mediasnak.com')
    #
    file = bucket.get_key(key)
    if file is None:
        return render_to_response('base.html', { 'error': 'This file key is invalid!' })
    #
    filename = file.get_metadata('filename')
    if filename is None:
        return render_to_response('base.html', { 'error': 'There was an error, the remote metadata on this file couldn\'t be found' })

    # check that this etag matches this key?    
    
    upload_time = datetime.utcnow()

    # Set the file status as uploaded in database
    file_entry.filename=filename
    file_entry.upload_time=upload_time
    file_entry.save()
    # Now everything for the file entry except view_count should now be filled in

    # Get the information for this file (which was just saved)
    # file_entry = MediaFile.objects.get(file_id=file_id)

    # Use render_to_response shortcut to fill out the upload.html template
    template_vars = {
        'bucket': bucket, 'key': key, 'etag': etag,
        'upload_time': upload_time, 'file_id': file_id, 'user_id': user_id, 'filename': filename
    }
    return render_to_response('upload-success.html', template_vars)