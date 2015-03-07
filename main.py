#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import webapp2
import handler
import re
import database
import time
import cache
from google.appengine.ext import db
import logging
import hmac
import hashlib
import string

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE= re.compile(r"^[\S]+@[\S]+\.[\S]+$")


'''check if username follow the regular expression rule'''
def valid_username(username):
	return USER_RE.match(username)

'''check if username follow the regular expression rule'''
def valid_password(password):
	return PASS_RE.match(password)

'''check if username follow the regular expression rule'''
def valid_email(email):
	return EMAIL_RE.match(email)



'''renders the page content from the database'''
class WikiPage(handler.Handler):

	def get(self, pagename):
		v = self.request.get('v')
		user_id = self.read_secure_cookie('user_id')	#check if the user is logged in
		if user_id:
			username = database.Users.get_by_id(int(user_id)).username
		else:
			username = ''

		page, time_last = cache.cache_get(pagename)	#get the latest page content from cache
		editpage = '/_edit'+pagename
		historypage = '/_history'+pagename
		if page == None:
			self.redirect(editpage)
		else:
			if v and v.isdigit():	#if there is version request, use it, if not, get the latest page
				pages = db.GqlQuery("select * from Page WHERE pagename=:1 ORDER by created DESC", pagename)
				content = list(pages)[int(v)].content
			else:
				content = page.content
			self.render('wikipage.html', content = content, editpage = editpage, username = username, historypage = historypage)



'''It renders the login form and validate user information, set the cookie so user is logged in'''
class Login(handler.Handler):

	'''the get pass to post method the referer page so user can return to that page after signup'''
	def get(self):
		next_url = self.request.headers.get('referer' , '/')
		self.render('login-form.html', next_url = next_url)


	'''renders the login form, validate information, goes back to where user was'''
	def post(self):
		next_url = str(self.request.get('next_url'))	#get the referer page from login get()
		if not next_url or ('/signup' in next_url):	#avoid dead cycle from signup and login
			next_url = '/'
		username = self.request.get('username')
		password = self.request.get('password')
		error = False
		u = database.Users.all().filter('username =', username).get()	#gets the information of the user form database
		if not u:   
			error = True
		else: 
			if not self.valid_pw(username, password, u.password):	#validate the secure password stored in the database with user type in
				error = True
		
		if error == True:
			self.render('login-form.html' , error = 'Invalid login.')
		else:
			self.set_secure_cookie('user_id', str(u.key().id()))	#set the secure cookie so user is logged in
			self.redirect(next_url)
			

'''clears the cookies and goes back to the page user was at'''
class Logout(handler.Handler):

	def get(self):
		next_url = self.request.headers.get('referer' , '/')
		self.response.headers.add_header(
			'Set-Cookie','%s=%s; Path=/' % ('user_id', ''))
		self.redirect(next_url)



'''The Signup renders a sigup form and creates a new user'''
class Signup(handler.Handler):

	'''the get pass to post method the referer page so user can return to that page after signup'''
	def get(self):
		next_url = self.request.headers.get('referer' , '/')
		self.render('signup.html', next_url = next_url)


	'''creates new user from the information provided by user'''
	def post(self):
		next_url = str(self.request.get('next_url'))
		logging.error('url is ' +next_url)
		if not next_url or ('/login' in next_url):	#avoids the dead cycle of going back and forth to login and signup
			next_url = '/'
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')
		username_error = ''
		password_error = ''
		verify_error = ''
		email_error = ''
		error = False
		
		if not valid_username(username):	#use valide_username() to check if it follow right format
			username_error = 'That\'s not a valid username.'
			error = True
		elif database.Users.all().filter('username =', username).get():	#check database if username exits
			error = True
			username_error='The username already exists.'
		
		if not valid_password(password):	#checks the password follow right format
			password_error = 'That wasn\'t a valid password.'
			error = True
		else:
			if password != verify:
				verify_error = 'Your passwords didn\'t match.'
				error = True
		
		if email:
			if not valid_email(email):	#checks email follow the email format
				email_error = 'That\'s not a valid email.'
				error = True

		all_message={'username': username, 'username_error' : username_error ,
					'password_error' : password_error, 'verify_error' : verify_error,
					'email': email, 'email_error' : email_error}

		if error is True:
			self.render("signup.html", **all_message)	#if this is error, the error message are shown
		else:
			pw_h = self.hash_pw(username, password)	#The password stored in Users object is the secure password
			u = database.Users(username = username , password = pw_h, email= email)
			u.put()
			self.set_secure_cookie('user_id', str(u.key().id()))   #set cookie so the user is logged in
			self.redirect(next_url)



'''If user is logged in, he/she can edit the page'''
class EditPage(handler.Handler):

	'''Find the content of the page with the pagename and render the form with the content in it'''
	def get(self, pagename):
		if pagename == '/login' or pagename == '/logout' or pagename == '/signup':
			self.render('prohibited.html')
			return

		cookie = self.read_secure_cookie('user_id')
		v = self.request.get('v')
		if not cookie:   #if not logged in, redirect page shows up
			self.render('redirect.html')
			return
		username = database.Users.get_by_id(int(cookie)).username

		if v and v.isdigit():	#if there is version request, the version is found by check the database
			pages  = db.GqlQuery("select * from Page WHERE pagename=:1 ORDER by created DESC", pagename)	#find all Page with pagename
			content = list(pages)[int(v)].content
		else:
			page, time_last = cache.cache_get(pagename)	#if no version request simply read from cache of the latest page
			if page == None:
				content = ''
			else:
				content = page.content
		viewpage = pagename
		historypage = '/_history' + pagename
		self.render('edit.html', viewpage = viewpage, content = content, username= username, historypage = historypage)


	'''the cache_edit() updates database, then redirect to the edited page with new content'''
	def post(self, pagename):
		content = self.request.get('content')
		cache.cache_edit(pagename, content)
		self.redirect(pagename)


'''reads from database the history of the page with the page name, and return the history'''
class History(handler.Handler):
	def get(self, pagename):
		user_id = self.read_secure_cookie('user_id')
		if user_id:
			username = database.Users.get_by_id(int(user_id)).username
		else:
			username = ''
		pages  = db.GqlQuery("select * from Page WHERE pagename=:1 ORDER by created DESC", pagename)
		pages = list(pages)	#list all the pages with the same pagename, thus the history
		editpage = '/_edit'+pagename
		viewpage = pagename
		self.render('history.html', pages = pages, editpage = editpage, viewpage = viewpage, username = username, length = len(pages))



PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

app = webapp2.WSGIApplication([
    ('/login',Login),
    ('/signup',Signup),
    ('/logout',Logout),
    ('/_edit'+PAGE_RE, EditPage),
    ('/_history'+PAGE_RE, History),
    (PAGE_RE, WikiPage),
], debug=True)
