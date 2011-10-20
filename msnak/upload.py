from django.utils import simplejson
from random import randrange
from base64 import urlsafe_b64encode, b64encode
from datetime import datetime, timedelta
from msnak.s3util import hmac_sign
import access_keys, os, mimetypes
from models import MediaFile # Database table for files
import exception

# Note: I know it's a one-line function which is only used once in the code
# but it's got a bit complex and has a seperate function than the rest of the code,
# and more deliberately, this gives us access to test it
#
def generate_unique_id():
    # You know how Youtube has those video IDs that look like "r_xHTXf-iIY"?
    # This line randomly generates one of those (it's just an 8 byte random value).
    
    value = urlsafe_b64encode(''.join([chr(randrange(255)) for x in xrange(8)]))[:11]
    while len(MediaFile.objects.filter(pk=value)) > 0: # If the ID already exists, generate another
        value = urlsafe_b64encode(''.join([chr(randrange(255)) for x in xrange(8)]))[:11]   
    return value

def upload_form_parameters(bucketname, user_id):

    file_id = generate_unique_id()

    # Put together a key
    s3_key = 'u/%s' % (file_id,)

    # Expiry date string in ISO8601 GMT format, one hour in the future:
    expiry = (datetime.utcnow() + timedelta(hours=1)).isoformat()+'Z'

    # Construct policy string from JSON. This ensures that if the user tries something sneaky such as
    # altering the hidden form fields, then the upload will be rejected.
    policy_str = simplejson.dumps({
        'expiration': expiry,
        'conditions': [
            {'key': s3_key},
            {'acl': 'private'},
            {'bucket': 's3.mediasnak.com'},
            ['starts-with', '$Content-Disposition', 'inline; filename='],
            ['starts-with', '$Content-Type', ''],
            {'success_action_redirect': 'http://%s/success' % (os.environ['HTTP_HOST'],)},
            ['starts-with', '$x-amz-meta-filename', ''],
            {'x-amz-meta-userid': user_id}
            ]
        })

    policy = b64encode(policy_str.encode('utf8'))
    signature = hmac_sign(policy) # Sign the policy
    
    # Save the file ID in the database, so that we can match it up when the upload is finished
    # and also ensure it was a valid upload
    # The filename, upload time and view count will be filled in later (just setting upload time to the current time for now)
    # User ID may also be checked later
    file_entry = MediaFile(file_id=file_id, uploaded=False, user_id=user_id, filename='', upload_time=datetime.utcnow(), view_count=0)
    file_entry.save()
    
    return { 'key': s3_key, 'aws_id': access_keys.key_id, 'policy': policy, 'signature': signature, 'return_host': os.environ['HTTP_HOST'], 'user_id': user_id }

def process_return_from_upload(bucketname, user_id, key, etag):

    file_id = key[2:] # slice 'u/' off the front

    # check database that this matches a valid upload
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # if the entry hasn't been created yet ...
        # What to do now?
        # Either user could re-upload the file,
        # or the system could simply create the file_id now instead assuming there's no reason not to
        #return {
        #    'error': "There seems to have been no file set-up for this upload."
        #}
        raise exception.MediasnakError("There seems to have been no file set-up for this upload.")
    except MediaFile.MultipleObjectsReturned:
        ## this error should never occur due to primary key constraint ##
        raise exception.MediasnakError("Apparently this file's ID, '" + file_id + "' has already finished uploading before.")
        
    if file_entry.uploaded:
        raise exception.MediasnakError("Sorry, this file has already been uploaded. Try going back and uploading a new file.")

    # Check the file upload belongs to this user
    if file_entry.user_id != user_id:
        raise exception.MediasnakError("Apparently this file upload wasn't requested by the logged-in user.")

    # Make sure this file-id hasn't been already used for another file somehow?
    # for instance, if the user reloads the page, the file information will be overridden

    # extract filename from s3
    # ..use key, or etag?
    import s3util
    metadata = s3util.get_s3_metadata(bucketname, key)
    if 'filename' not in metadata or 'userid' not in metadata:
        raise exception.MediasnakError('There is some metadata missing from the file on S3! This shouldn\'t happen.')
    
    filename = metadata['filename']
    
    # Check the file setup on S3 with this key is for the current user
    if metadata['userid'] != user_id:
        raise exception.MediasnakError("Apparently this file upload wasn't requested by the logged-in user.")
    
    # check that this etag matches this key?
    
    upload_time = datetime.utcnow()

    # Set the file status as uploaded in database
    file_entry.filename=filename
    file_entry.upload_time=upload_time
    file_entry.uploaded=True
    file_entry.save()
    # Now everything for the file entry except view_count should now be filled in
    
    # Update mimetype stored on S3
    s3util.update_s3_metadata(bucketname, key, {'Content-Type': mimetypes.guess_type(filename)[0]})
    
    return {
        'url': '/download?fileid='+file_id,
        'upload_time': upload_time,
        'filename': filename,
        'mimetype': mimetypes.guess_type(filename)[0]
    }

def purge_uploads():
    MediaFile.objects.filter(upload_time__lte=(datetime.utcnow()-timedelta(minutes=30))).delete()
