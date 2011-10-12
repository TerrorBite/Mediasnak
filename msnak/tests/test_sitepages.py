
from django.utils.unittest import TestCase # This is django's copy of the unittest included in python 2.7 (we're using an older version). This one also clears the database before each test
from django.test import TestCase # Has stuff like assertContains, would like to use, but is giving errors when included
from unittest import TestCase

from django.test.client import Client # Client lets us test django's generated pages without having to load them through a server to a browser
from msnak.models import MediaFile # Import our database model

import urllib2 #extended URL handling library
import msnak.s3util

class TestSite(TestCase):
    key1="u/tests/file1"
    key2="u/tests/file2"
    key3="u/tests/file3"
    key4="u/tests/pQv-O2sFKi8"
    
    def setUp(self):
        # Manually load the database
        # The tests folder on S3 is used for holding test files
        MediaFile(file_id="u/tests/file1", user_id=0, filename="testfile1.png", upload_time="2011-01-01 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/file2", user_id=0, filename="duplicatefilename.png", upload_time="2011-01-01 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/file3", user_id=0, filename="duplicatefilename.png", upload_time="2011-01-01 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/pQv-O2sFKi8", user_id=0, filename="Jellyfish.jpg", upload_time="2011-01-01 00:00", view_count=100).save()
        self.client1 = Client()
        
        
    def testHomePage(self):
        "Test the home page exists"
        response = self.client1.get('/', {})
        self.assertEqual(response.status_code, 200)
        
