
import exception, access_keys
from models import MediaFile
from boto.s3.connection import S3Connection

def delete_file(bucketname, user_id, file_id):
    """
    Raises MediaFile.DoesNotExist
           MediaFile.MultipleObjectsReturned
    """
    print "X-Debug-Header: Entered delete_file function"
    
    #check that the file actually exists
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # Essentially a 404
        raise exception.MediasnakError("The file ID that you provided does not exist in the database.")
    except Exception, e:
        raise exception.MediasnakError("An unknown error occurred: %s" % (repr(e),))


    if file_entry.user_id != user_id:
        # Essentially a 403
        raise exception.MediasnakError("You are trying to access a file that you didn't upload.")

    #delete the file off S3
    botoconn = S3Connection(access_keys.key_id, access_keys.secret, is_secure=False)
    bucket = botoconn.create_bucket(bucketname)
    bucket.delete_key('u/'+file_id)
    
    #delete file off database
    try:
        file_entry.delete()
    except NotSavedError:
        raise exception.MediasnakError("Failed to delete file - maybe it doesn't exist?")

    #done!
