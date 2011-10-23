from django.db import models as m

class User(m.Model):
    user_id = m.IntegerField()
    username = m.CharField(max_length=32)
    passwd_hash = m.CharField(max_length=40)
    passwd_salt = m.CharField(max_length=40)

class MediaFile(m.Model):
    file_id = m.CharField(max_length=12, primary_key=True)
    uploaded = m.BooleanField()
    user_id = m.CharField(max_length=128)
    filename = m.CharField(max_length=128)
    upload_time = m.DateTimeField()
    view_count = m.IntegerField()
    comment = m.CharField(max_length=1000) # fairly large comments allowed
    category = m.CharField(max_length=12)
    tags = m.CharField(max_length=1000)
    has_thumb = m.BooleanField()
