from google.appengine.api import users

def get_user_nickname():
    user = users.get_current_user()
    if user:
        return user.nickname()
    else:
        return None

def is_logged_in():
    if users.get_current_user(): return True
    return False

def template_vars(vdict=None):
    "Adds variables required for the base template to display login/logout links."
    vdict = vdict or {}
    user = users.get_current_user()
    if user:
        vdict.update({'username': user.nickname(), 'logout_url': users.create_logout_url('/')})
    else:
        vdict.update({'login_url': users.create_login_url('/')})
    return vdict

def get_user_id():
    user = users.get_current_user()
    if user:
        return user.user_id()
    else:
        return None
