
from models import MediaFile # Database table for files
import exception

# Convenience function
def get_file_data(file_entry):
    return {
        'file_id' : file_entry.file_id, # can be used in a URL to access the information page for this file
        'file_title' : file_entry.title,
        'filename' : file_entry.filename,
        'upload_time' : file_entry.upload_time,
        'view_count' : file_entry.view_count
        }
    # alternative dictionary syntax, apparently:
    # dict( a = b, c = d )

def get_user_file_list(user_id, bucketname, orderby=None):

    file_entries = MediaFile.objects.filter(user_id=user_id).filter(uploaded=True) # retrieve the user's items
    
    # Currently in links, ['name', 'type', 'date', 'cat', 'meta'], could convert them
    if orderby and orderby in ['title', 'filename', 'upload_time', 'view_count', 'category']:
        file_entries = file_entries.order_by(orderby)
    
    # file_list_entries is the file information which will be used by the template
    file_list_entries = []
    filenames = []
    for file_entry in file_entries:
        file_list_entries.append(get_file_data(file_entry))
    
    # Use render_to_response shortcut to fill out the HTML template
    return {
        'file_list_entries': file_list_entries
    }
    
    
def search_files(bucketname, user_id, search_by, search_term, orderby=None):
    file_entries = MediaFile.objects.filter(user_id=user_id).filter(uploaded=True)
    
    # Currently in links, ['name', 'type', 'date', 'cat', 'meta'], could convert them
    if orderby and orderby in ['title', 'filename', 'upload_time', 'view_count', 'category']:
        file_entries = file_entries.order_by(orderby)
        
    results = []

    #avaliable fields: file_id, filename, upload_time, view_count, comment, category, tags
    #default: filename, upload_time, comment, tags
    if search_by == "default":
        for item in file_entries:
            #neaten this up later
            if (search_term in item.filename) or \
            (item.title and search_term in item.title) or \
            (item.tags and search_term in item.tags) or \
            (item.comment and search_term in item.comment) or \
            (search_term in str(item.upload_time)):
                results.append(get_file_data(item))
    elif search_by == "title":
        for item in file_entries:
            if item.title and search_term in item.title:
                results.append(get_file_data(item))
    elif search_by == "filename":
        for item in file_entries:
            if search_term in item.filename:
                results.append(get_file_data(item))
    elif search_by == "uploadtime":
        for item in file_entries:
            if search_term in str(item.upload_time):
                results.append(get_file_data(item))
    elif search_by == "comment":
        for item in file_entries:
            if item.comment and search_term in item.comment:
                results.append(get_file_data(item))
    elif search_by == "tags":
        for item in file_entries:
            if item.tags and search_term in item.tags:
                results.append(get_file_data(item))
    elif search_by == "category":
        for item in file_entries:
            if search_term == item.category:
                results.append(get_file_data(item))
    else:
        raise exception.MediasnakError("That is an invalid category to search by.");
        #return render_to_response('base.html',{'error':'That is an invalid category to search by'})

    
    # 'info': len(results) + ' results for ' + search_term
    if len(results) < 1:
        return {
            'info': 'No search results returned.',
            'file_list_entries': results # return the empty list, too
        }
        #return render_to_response('base.html',{'info':'No search results returned'})
    else:
        return {
            'info': "Searching " + search_by + " for '" + search_term + "', " + str(len(results)) + " search results returned.",
            'file_list_entries': results
        }
