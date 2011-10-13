from google.appengine.api import users

def checkLogin():
    user = users.ger_current_user()
    if user:
        message = "Welcome " + user.nickname() + " (<a href=\"" +\
                  users.create_logout_url() + "\">Log Out</a>"
    else:
        message = "<a href=\"" + users.create_login_url + "\">Sign in!</a>"

    return message
