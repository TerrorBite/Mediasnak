from django.utils.unittest import TestCase # This is django's copy of the unittest included in python 2.7 (we're using an older version). This one also clears the database before each test
from django.test import TestCase # Has stuff like assertContains, would like to use, but is giving errors when included
from unittest import TestCase

from django.test.client import Client # Client lets us test django's generated pages without having to load them through a server to a browser
from msnak.models import MediaFile # Import our database model

import urllib2 #extended URL handling library
import msnak.s3util

import msnak.listfiles

class TestListFiles(TestCase):
    key1="u/tests/file1"
    key2="u/tests/file2"
    key3="u/tests/file3"
    key4="u/tests/pQv-O2sFKi8"
    
    def setUp(self):
        self.client1 = Client()
        
    def testListOneFile(self):
        MediaFile(file_id="u/tests/file1", user_id=0, filename="testfile1.png", upload_time="2011-01-01 00:00", view_count=100).save()
        
        files = msnak.listfiles.get_user_file_list("0", "s3.mediasnak.com")
        
        self.assertTrue( len(files['file_list_entries']), 1 )
        self.assertTrue( files['file_list_entries'][0]['name'], "testfile1.png" )
        
        
    def testListFilePage(self):
        "Test the page exists"
        response = self.client1.get('/files', {})
        self.assertEqual(response.status_code, 200)
        
        
    def testListFilesView(self):
        
        self.assertTrue( , )