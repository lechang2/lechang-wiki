from google.appengine.api import memcache
from google.appengine.ext import db
import database
import time
import logging


'''The method gets the cache of page with pagename. If not cached yet, it reads from data base'''
def cache_get(pagename):
    result = memcache.get(pagename)
    if result is None:  #no cookie
        page = db.GqlQuery("select * from Page WHERE pagename=:1" , pagename).get()
        if page == None:  #no data or cookie
            return (None, None)
        else:
            time_last = page.created 
            memcache.set(pagename, (page, time_last))   #the cache is stored with additional information of last time cache was edited'
    else:
        page, time_last = result   

    return (page, time_last) 


'''The method edits the page object. It basically adds a new page object into database each time edited.
   It also update the cache of the page with pagename to the latest edit'''    
def cache_edit(pagename, content):
    time_last = time.time()
    if not content:
        content = ' '
    page = database.Page(pagename = pagename, content = content)        
    page.put()
    memcache.set(pagename, (page, content))

    return (page, time_last) 