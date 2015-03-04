import webapp2
import jinja2
import os
import hmac
import random
import hashlib
import logging
import string


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env =  jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape= True)

secret = 'This is a secret'     #This is the secret for the scure value cookie


'''uses hmac to create a secure value using a secret key value from above'''
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


'''use the make_secure_val function to check if the secure value really 
reflect the value from this message, if yes, resturn the value'''
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

'''The helper functions used in the main function to render html,
read cookies, set cookies, valid and create secure password'''
class Handler(webapp2.RequestHandler):

    '''output the html created by the template'''
    def write(self, *a, **kw):
        self.response.out.write(*a,**kw)

    
    '''use the template and input variables to render the pages'''
    def render_str(self, template, **params):
        t=jinja_env.get_template(template)
        return t.render(params)

    
    '''takes the variables for templates and call write to write html'''
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    
    '''use function make_secure_val() to set secure values into cookies and set the cookie'''
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    
    '''use the check_secure_val() to check if value is not edited by 
        unauthorized person, and return the value if it is not edited'''
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    
    '''makes a random value for password'''
    def make_salt(self):
        return ''.join(random.choice(string.letters) for x in xrange(5))

    
    '''create secure password using user input password to combine with salt. Return the secure password and the salt used'''
    def hash_pw(self, name, password, salt = None):
        if not salt:
            salt = self.make_salt()   #if user passes in a salt, use user's salt, else, create a salt
        h = hashlib.sha256(name + password + salt).hexdigest()+'|'+salt
        return h

    
    '''use the salt in the secure password and user's password input to verify 
    that the password is same as the one in secure password
    return true if it is same password as the the secure password, false if not'''
    def valid_pw(self, name, password, pw_h):
        salt = pw_h.split('|')[1]
        if pw_h == self.hash_pw(name, password, salt):
            return True
        else:
            return False
