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