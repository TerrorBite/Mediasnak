from django.utils.unittest import TestCase # This is django's copy of the unittest included in python 2.7
from django.test.client import Client
#from django.test import TestCase # Has stuff like assertContains, would like to use, but is giving errors when included

from msnak.models import MediaFile

class TestUpload(TestCase):
    fixtures = ['msnak_testfixture.json']

    def setUp(self):
        self.c = Client()

    # Must test to see that the key that gets returned each upload-request is different
    # Cue: Refactoring into seperate functions
        
    def testRequestUploadPage(self):
        "Test the upload page exists"
        response = self.c.get('/upload', {})
        
        self.assertEqual(response.status_code, 200)
        
        #self.assertContains(response, 'Upload')
        #self.assertContains(response, 'Upload a file:')
        self.assertEqual('Upload' in response.content, True)
        self.assertEqual('Upload a file:' in response.content, True)
        
    def testSuccessBlankInput(self):
        "Test that if the success page is went to without any input, redirect to upload page"
        response = self.c.get('/success', {})
        
        self.assertEqual(response.status_code, 302)
        #self.assertRedirects(response,  'upload')

    def testSuccessWrongBucket(self):
        "Test what happens if the wrong bucketname is given when returning from upload"
        response = self.c.get('/success',
            {'bucket': 's3.blah.com', 'etag': '"735ab4f94fbcd57074377afca324c813"', 'key': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('error' in response.content, True)
        
    def testSuccessKeyNotOnS3(self):
        "Test what happens if a random key is given when returning from upload"
        response = self.c.get('/success',
            {'bucket': 's3.mediasnak.com', 'etag': '"735ab4f94fbcd57074377afca324c813"', 'key': 'fakekey'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('error' in response.content, True)
    
    def testSuccessKeyAlreadyUsed(self):
        "Test what happens if an already taken key is given when returning from upload"
        # This 'u/m0fd-XGR1kw' key should exist on s3
        response = self.c.get('/success',
            {'bucket': 's3.mediasnak.com', 'etag': '"735ab4f94fbcd57074377afca324c813"', 'key': 'u/m0fd-XGR1kw'})
        self.assertEqual(response.status_code, 200)
        #self.assertEqual('error' in response.content, True)

    def testPerformUpload(self):
        "Test performing a full upload"
        
        response = self.c.get('/upload', {})
        #response.text.contains()
        #{'key': key, 'aws_id': access_keys.key_id, 'policy': policy, 'signature': signature})
        #key = response.context['key'];
        key = 'test'
        #self.assertEqual(response.context['aws_id'], access_keys.key_id)
        #self.assertEqual(response.context['signature'], hmac_sign(policy))
        
        self.assertEqual(response.templates, [])
        # since for some reason the template list is blank, also the context is blank
        
        #self.assertEqual(response.templates[0].name, 'upload.html')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        
        #'bucket': bucket, 'key': key, 'etag': etag,
        #'upload_time': upload_time, 'file_id': file_id, 'user_id': user_id, 'filename': filename
        response = self.c.get('/success',
            {'bucket': 's3.mediasnak.com', 'etag': '"735ab4f94fbcd57074377afca324c813"', 'key': key})
        self.assertEqual(response.status_code, 200)
        #self.assertEqual(response.context['bucket'], 's3.mediasnak.com')
        #self.assertEqual(response.context['key'], key)
        #self.assertEqual(response.context['etag'], '"735ab4f94fbcd57074377afca324c813"')
        #self.assertEqual(datetime.utcnow() - response.context['upload_time'] < 100, True)
        #self.assertEqual(response.context['filename'], 'testfile.txt')
        
        
        #self.assertEqual('s3.mediasnak.com' in response.content, True)
        #self.assertEqual(key in response.content, True)
        #self.assertEqual('"735ab4f94fbcd57074377afca324c813"' in response.content, True)

    # ACCEPTANCE CRITERIA, STORY 1
    def testPerformUploadImage(self):
        #Acceptance Criteria
        # A 'browse' option is shown to find the file
        # File is located on the server
        # File is handled using secure protocols, such as  https 
        
        response = self.c.get('/upload', {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('<input type="file" ' in response.content, True)
        
        #upload
        _filename = "test.txt"
        
        self.assertNotEqual(MediaFile.objects.get(filename="test.txt"), None)
        
        from boto.s3.connection import S3Connection
        botoconn = S3Connection(access_keys.key_id, access_keys.secret)
        bucket = botoconn.create_bucket('s3.mediasnak.com')
        file = bucket.get_key(key)
        self.assertNotEqual(file, None)
        self.assertEqual(file.get_metadata('filename'), _filename)
        
        pass
        
    # ACCEPTANCE CRITERIA, STORY 2
    def testPerformUploadAudio(self):
        pass
        
    # ACCEPTANCE CRITERIA, STORY 3
    def testPerformUploadVideo(self):
        pass
        