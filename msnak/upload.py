from django.utils import simplejson
from random import randrange
from base64 import urlsafe_b64encode, b64encode
from datetime import datetime, timedelta
from msnak.s3util import hmac_sign
import access_keys
from models import MediaFile # Database table for files
import exception

# Note: I know it's a one-line function which is only used once in the code
# but it's got a bit complex and has a seperate function than the rest of the code,
# and more deliberately, this gives us access to test it
#
def generate_unique_id():
    # You know how Youtube has those video IDs that look like "r_xHTXf-iIY"?
    # This line randomly generates one of those (it's just an 8 byte random value).
    return urlsafe_b64encode(''.join([chr(randrange(255)) for x in xrange(8)]))[:11]


def upload_form_parameters(bucketname, user_id):

    uniq = generate_unique_id()

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
    
    return { 'key': key, 'aws_id': access_keys.key_id, 'policy': policy, 'signature': signature }

def process_return_from_upload(bucketname, user_id, key, etag):

    file_id = key
    
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
        #return {
        #    'error': "There seems to have been no file set-up for this upload."
        #}
        raise MediasnakError("There seems to have been no file set-up for this upload.")
    except MediaFile.MultipleObjectsReturned:
        ## this error will be reached if the user hits the back button and tries to upload again ##
        # means a file may be overridden in s3
        #return {
        #    'error': "Apparently this file's ID has already finished uploading before.",
        #    'bucket': bucketname, 'key': key, 'etag': etag,
        #    'file_id': file_id, 'user_id': user_id
        #}
        raise MediasnakError("Apparently this file's ID, '" + file_id + "' has already finished uploading before.")

    # could check the file upload belongs to this user
    if file_entry.user_id != user_id:
        raise MediasnakError("Apparently this file upload wasn't requested by the logged-in user.")

    # Make sure this file-id hasn't been already used for another file somehow?
    # for instance, if the user reloads the page, the file information will be overridden

    # extract filename from s3
    # ..use key, or etag?
    import s3util
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
    
    return {
        'url': url,
        'upload_time': upload_time, 'filename': filename
    }