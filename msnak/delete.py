
import exception

def delete_file(bucketname, user_id, file_id):
"""
Raises MediaFile.DoesNotExist
       MediaFile.MultipleObjectsReturned
"""

    #check that the file actually exists
    try
        file_entry = MediaFile.objects.get(file_id=file_id)
    except MediaFile.DoesNotExist:
        return exception.MediasnakError("The file does not exist.")

    #delete the file off S3
    botoconn = S3Connection(access_keys.key_id, access_keys.secret)
    bucket = botoconn.create_bucket(bucketname)
    bucket.delete_key('u/'+file_id)
    
    #delete file off database
    try:
        file_entry.delete()
    except NotSavedError:
        raise exception.MediasnakError("The file does not exist.")

    #done!