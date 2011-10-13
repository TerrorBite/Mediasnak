from django.utils.unittest import TestCase # This is django's copy of the unittest included in python 2.7 (we're using an older version). This one also clears the database before each test
from django.test import TestCase # Has stuff like assertContains, would like to use, but is giving errors when included
from unittest import TestCase
from msnak.models import MediaFile # Import our database model
from msnak.listfiles import search_files

class TestSearch(TestCase):
    #assertTrue()
    #assertEquals()

    def setUp(self):
        
        MediaFile(file_id="u/tests/file1", user_id=0, filename="test.png", upload_time="2000-08-03 00:00", view_count=100).save()
        MediaFile(file_id="u/tests/file2", user_id=0, filename="duplicatefilename.png", upload_time="2011-08-16 00:00", view_count=7).save()
        MediaFile(file_id="u/tests/file3", user_id=0, filename="duplicatefilename.png", upload_time="2000-04-25 00:00", view_count=20).save()
        MediaFile(file_id="u/tests/random", user_id=0, filename="somefile.jpg", upload_time="2000-02-20 00:00", view_count=90).save()
        MediaFile(file_id="u/tests/pQv-O2sFKi8", user_id=0, filename="Jellyfish.jpg", upload_time="2003-09-16 00:00", view_count=350).save()

    #couple of searches searching the database for everything
    def testSearchEverything1(self):
        results = search_files("s3.mediasnak.com",0,"default","file")
        count = 0
        #for item in results:
        #    count = count + 1
        count = len(results)
        self.assertEquals(count, 4)
        
    def testSearchEverything2(self):
        results = search_files("s3.mediasnak.com",0,"default","1")
        count = 0
        for item in results:
            count = count + 1
        self.assertEquals(count,3)

    #couple of searches searching the database for filenames
    def testSearchFileName1(self):
        results = search_files("s3.mediasnak.com",0,"filename",".jpg")
        count = 0
        for item in results:
            count = count + 1
        self.assertEquals(count,2)

    def testSearchFileName2(self):
        results = search_files("s3.mediasnak.com",0,"filename","file")
        count = 0
        for item in results:
            count = count + 1
        self.assertEquals(count,3)

    #couple of searches searching the database for upload time
    def testSeachUploadTime1(self):
        results = search_files("s3.mediasnak.com",0,"uploadtime","1")
        count = 0
        for item in results:
            count = count + 1
        self.assertEquals(count,2)

    def testSeachUploadTime2(self):
        results = search_files("s3.mediasnak.com",0,"uploadtime","2000")
        count = 0
        for item in results:
            count = count + 1
        self.assertEquals(count,3)
