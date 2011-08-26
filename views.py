"""
Mediasnak Django Views

Contains the custom Django views for the Mediasnak application.
"""

import access_keys
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from random import randrange
from base64 import urlsafe_b64encode, b64encode
from datetime import datetime, timedelta
from s3util import hmac_sign

def upload_form(request):
    "Produces an upload form for submitting files to S3."

    user_id = 0 # dummy value for now until we get multiple user support

    # You know how Youtube has those video IDs that look like "r_xHTXf-iIY"?
    # This line randomly generates one of those (it's just an 8 bit random value).
    uniq = urlsafe_b64encode(''.join([chr(randrange(255)) for x in xrange(8)]))[:11]

    # Put together a key
    key = 'u/{0}/{1}'.format(user_id, uniq)

    # Expiry date string in ISO8601 GMT format, one hour in the future:
    expiry = (datetime.utcnow() + timedelta(hours=1)).isoformat()+'Z'
    
    # Construct policy string from JSON. This ensures that if the user tries something sneaky such as
    # altering the hidden form fields, then the upload will be rejected.
    policy_str = simplejson.dumps({
        'expiration': expiry,
        'conditions': [
            {'acl': 'private'},
            {'bucket': 's3.mediasnak.com'},
            {'Content-Disposition': 'attachment; filename=${filename}'},
            ['starts-with', '$Content-Type', ''],
            {'success-action-redirect': 'http://www.mediasnak.com/success'},
            {'key', key}
            ]
        })

    policy = b64encode(policy_str.encode('utf8'))
    signature = hmac_sign(policy)

    # Use render_to_response shortcut
    return render_to_response('upload.html', {'key': key, 'aws_id': access_keys.key_id, 'policy': policy, 'signature': signature})
