from django.utils.unittest import TestCase # This is django's copy of the unittest included in python 2.7
from django.test.client import Client
#from django.test import TestCase # Has stuff like assertContains, would like to use, but is giving errors when included

from msnak.models import MediaFile

class TestUpload(TestCase):
    fixtures = ['msnak_testfixture.json']
   
    def setUp(self):
    
        self.c = Client()
        
    def testDatabaseSetup(self):
    
        # Load the test fixture
        # The following lets us call django-admin.py (manage.py) commands from python
        from django.core.management import call_command
        # Equivalent to running 'manage.py loaddata'
        call_command('loaddata', 'msnak_testfixture.json')
        
        self.assertNotEqual(MediaFile, None)
        self.assertNotEqual(MediaFile.objects, None)
        self.assertNotEqual(MediaFile.objects.all(), None)
        self.assertEqual(len(MediaFile.objects.all()), 2) # This fixture should define 2 rows in the MediaFile table
        file_entry = MediaFile.objects.all()
        
    def testDatabaseSetupAnother(self):
        self.assertNotEqual(MediaFile, None)
        self.assertNotEqual(MediaFile.objects, None)
        self.assertNotEqual(MediaFile.objects.all(), None)
        self.assertEqual(len(MediaFile.objects.all()), 2) # This fixture should define 2 rows in the MediaFile table
        file_entry = MediaFile.objects.all()