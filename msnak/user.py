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

def template_vars(vars={}):
    "Adds variables required for the base template to display login/logout links."
    user = users.get_current_user()
    if user:
        vars.update({'username': user.nickname(), 'logout_url': users.create_logout_url('/')})
    else:
        vars.update({'login_url': users.create_login_url('/')})
    return vars

def get_user_id():
    user = users.get_current_user()
    if user:
        return user.user_id()
    else:
        return None