
import exception, access_keys
from models import MediaFile
from boto.s3.connection import S3Connection

def delete_file(bucketname, user_id, file_id):
    """
    Raises MediaFile.DoesNotExist
           MediaFile.MultipleObjectsReturned
    """
    
    #check that the file actually exists
    try:
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        # Essentially a 404
        return exception.MediasnakError("The file does not exist.")

    if file_entry.user_id != user_id:
        # Essentially a 403
        return exception.MediasnakError("You are trying to access a file that you didn't upload.")

    #delete the file off S3
    botoconn = S3Connection(access_keys.key_id, access_keys.secret, is_secure=False)
    bucket = botoconn.create_bucket(bucketname)
    bucket.delete_key('u/'+file_id)
    
    #delete file off database
    try:
        file_entry.delete()
    except NotSavedError:
        raise exception.MediasnakError("The file does not exist.")

    #done!
