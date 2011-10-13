
from models import MediaFile # Database table for files
from s3util import sign_url
import exception

def get_user_file_list(user_id, bucketname):

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
            'download_url' : sign_url(bucketname, file.file_id),
            'name' : file.filename,
            'upload_time' : file.upload_time,
            'view_count' : file.view_count
            }
        )
        # alternative dictionary syntax, apparently:
        # dict( a = b, c = d )
    
    # Use render_to_response shortcut to fill out the HTML template
    return {
        'file_list_entries': file_list_entries
    }
    
    
def search_files(bucketname, user_id, search_by, search_term):
    file_entries = MediaFile.objects.filter(user_id=user_id)
    results = []

    #expand this as we add extra fields (eg. author etc)
    if search_by == "default":
        for item in file_entries:
            #neaten this up later
            if (search_term in item.filename) or (search_term in str(item.upload_time)):
                results.append(
                    {
                    'file_id' : item.file_id, # can be used in a URL to access the information page for this file
                    'download_url' : sign_url(bucketname, item.file_id),
                    'name' : item.filename,
                    'upload_time' : item.upload_time,
                    'view_count' : item.view_count
                    }
                )
    elif search_by == "filename":
        for item in file_entries:
            if search_term in item.filename:
                results.append(
                    {
                    'file_id' : item.file_id, # can be used in a URL to access the information page for this file
                    'download_url' : sign_url(bucketname, item.file_id),
                    'name' : item.filename,
                    'upload_time' : item.upload_time,
                    'view_count' : item.view_count
                    }
                )
    elif search_by == "uploadtime":
        for item in file_entries:
            if search_term in str(item.upload_time):
                results.append(
                    {
                    'file_id' : item.file_id, # can be used in a URL to access the information page for this file
                    'download_url' : sign_url(bucketname, item.file_id),
                    'name' : item.filename,
                    'upload_time' : item.upload_time,
                    'view_count' : item.view_count
                    }
                )
    else:
        raise MediasnakError("That is an invalid category to search by.");
        #return render_to_response('base.html',{'error':'That is an invalid category to search by'})

    
    # 'info': len(results) + ' results for ' + search_term
    if len(results) < 1:
        return {
            'info': 'No search results returned.'
        }
        #return render_to_response('base.html',{'info':'No search results returned'})
    else:
        return {
            'info': "Searching " + search_by + " for '" + search_term + "', " + str(len(results)) + " search results returned.",
            'file_list_entries': results
        }
