
import exception

def delete_file(bucketname, user_id, file_id):
"""
Raises MediaFile.DoesNotExist
       MediaFile.MultipleObjectsReturned
"""

    ##check that the file actually exists
    #try
    #    file_entry = MediaFile.objects.get(file_id=file_id)
    #except MediaFile.DoesNotExist:
    #    return MediasnakError("The file does not exist.")
    #except MediaFile.MultipleObjectsReturned:
    #    return MediasnakError("There are multiple files by this file_id.")

    key_name = 'u/'+file_id
    
    #delete the file off S3
    botoconn = S3Connection(access_keys.key_id, access_keys.secret)
    bucket = botoconn.create_bucket(bucketname)
    bucket.delete_key(key_name)
    
    #delete file off database
    try:
        MediaFile.objects.get(file_id__exact=file_id).delete()
    except NotSavedError:
        raise MediasnakError("The file does not exist.")
        #return render_to_response('base.html',{'error':'The file does not exist.'})

    #done!