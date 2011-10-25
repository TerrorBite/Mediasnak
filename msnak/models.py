from django.db import models as m

class User(m.Model): # CURRENTLY UNUSED.
    # could be used in future
    user_id = m.IntegerField() # Primary key: Google-defined User ID
    first_visit = m.DateTimeField() # Date this record was created
    latest_visit = m.DateTimeField() # Date of user's most recent use of the site
    prefs = m.CharField(max_length=1024) # Perhaps a pickled preferences object could be stored here?
    tag_index = m.CharField(max_length=1024) # Keeps track of a user's tags, use to create a tag cloud?

class MediaFile(m.Model):
    # Important file entry data
    file_id = m.CharField(max_length=12, primary_key=True) # Primary key: File ID
    user_id = m.CharField(max_length=128) # User ID that owns the file (foreign key?)
    upload_time = m.DateTimeField() # Time that the upload was initiated or completed
    uploaded = m.BooleanField() # Is the file upload complete, or is this a placeholder entry?
    has_thumb = m.BooleanField() # True if the file has a custom, non-generic thumbnail
    # System metadata
    filename = m.CharField(max_length=128) # Original filename of the file
    category = m.CharField(max_length=12) # System-defined category (image/audio/video/other)
    view_count = m.IntegerField() # Number of times the file has been downloaded
    # User-defined metadata
    title = m.CharField(max_length=128, null=True) # Display title
    creator = m.CharField(max_length=128, null=True) # i.e. "Artist" field
    collection = m.CharField(max_length=128, null=True) # i.e. "Album" field
    comment = m.CharField(max_length=1000, null=True) # User-defined comment; fairly large comments allowed
    tags = m.CharField(max_length=1000, null=True) # Tags for the file (comma-separated string)
