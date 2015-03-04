from google.appengine.ext import db
import re

class Page(db.Model):
	content = db.TextProperty(required = True)
	pagename = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class Users(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = False)

	'''Class method of using username to find the user, return the user found'''
	def by_name(cls, username):
		u = Users.all().filter('username =', username).get()
		return u


#welcome = Page(pagename = '/luffy', content = 'Hi, welcome!')
#welcome.put()