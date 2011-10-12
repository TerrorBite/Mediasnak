from django.utils.unittest import TestCase # This is django's copy of the unittest included in python 2.7 (we're using an older version). This one also clears the database before each test
from django.test import TestCase # Has stuff like assertContains, would like to use, but is giving errors when included
from unittest import TestCase
from msnak.models import MediaFile # Import our database model

class TestSearch(TestCase):

    def setUp(self):
        MediaFile(file_id="u/tests/file1", user_id=0, filename="testfile1.png", upload_time="2011-01-01 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/file2", user_id=0, filename="duplicatefilename.png", upload_time="2011-01-01 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/file3", user_id=0, filename="duplicatefilename.png", upload_time="2011-01-01 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/pQv-O2sFKi8", user_id=0, filename="Jellyfish.jpg", upload_time="2011-01-01 00:00", view_count=100).save()

    #couple of searches searching the database for everything
    def searchEverything1(self):
        #self.assertTrue()
        pass

    def searchEverything2(self):
        pass

    #couple of searches searching the database for filenames
    def searchFileName1(self):
        pass

    def searchFileName2(self):
        pass
