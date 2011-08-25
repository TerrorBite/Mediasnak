"""
S3 Utilities

Contains useful functions for interacting with Amazon S3.
"""

import hmac, hashlib, urllib, base64, time

ACCESS_KEY = 'AKIAJUNFZFBBBS5EUM5A'
SECRET_KEY = '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'

URL_DEFAULT=0
URL_SUBDOM=1
URL_CUSTOM=2

def sign_url(bucket, key, expiry=3600, method='GET', format=0, secure=False):
    """
    Generates a signed URL for use with Amazon S3.
    
    bucket: This is the name of the bucket to use.
    
    key: The key within the bucket that we should return a URL to.
    
    expiry: Number of seconds that the URL should be valid for. For example,
        3600 will cause the URL to work for no longer than one hour.
    
    method: The HTTP method used for the URL. Default is "GET".
    
    format: This specifies the format of the URL to return. Default is URL_DEFAULT.
        URL_DEFAULT: Specifies a URL of the form http://s3.amazonaws.com/bucketname/key
        URL_SUBDOM: Specifies a URL of the form http://bucketname.s3.amazonaws.com/key
        URL_CUSTOM: Soecifies a custom-domain URL of the form http://bucketname/key. Note: This
            requires the bucket name to be in the form of a FDQN.
        
    secure: Should we return a Secure HTTP (https://) URL? Note, this will force
        format to be URL_FORMAT_DEFAULT to ensure correct certificate validation.
        By default, this is false (regular http).
    """
    
    host='s3.amazonaws.com'
    path = '/'+bucket+'/'+key
    canon_path = path
    
    if not secure:
        if format==URL_SUBDOM:
            host = bucket+'.s3.amazonaws.com'
            path = '/'+key
        elif format==URL_CUSTOM:
            host = bucket
            path = '/'+key
    
    # First, work out the expiry time
    expiry = str(int(time.time()) + expiry)
    
    # These are unused:
    content_md5 = ''
    content_type = ''
    canon_headers = ''
    
    # Work out the string to hash
    string = '{0}\n{1}\n{2}\n{3}\n{4}{5}'.format(method, content_md5, content_type, expiry, canon_headers, canon_path)
    
    # Calculate our signature
    signature = base64.b64encode(hmac.new(SECRET_KEY, string.encode('utf8'), hashlib.sha1).digest())
    
    # Work out our parameters
    params = urllib.urlencode({'AWSAccessKeyId': ACCESS_KEY, 'Signature': signature, 'Expires': expiry})
    
    return '{0}{1}{2}?{3}'.format('https://' if secure else 'http://', host, path, params)
    
