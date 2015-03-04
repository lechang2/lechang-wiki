from google.appengine.api import memcache
from google.appengine.ext import db
import database
import time
import logging


'''The method gets the cache of page with pagename. If not cached yet, it reads from data base'''
def cache_get(pagename):
    if memcache.get(pagename) is None:
        page = db.GqlQuery("select * from Page WHERE pagename=:1" , pagename).get()
        if page == None:
            return (None, None)
        else:
            time_last = page.created 
            memcache.set(pagename, (page, time_last))   #the cache is stored with additional information of last time cache was edited'
    else:
        page, time_last = memcache.get(pagename)   

    return (page, time_last) 


'''The method edits the page object. It basically adds a new page object into database each time edited.
   It also update the cache of the page with pagename to the latest edit'''    
def cache_edit(pagename, content):
    client = memcache.Client()    
    client.gets(pagename)   #This method of gets() get the cache pagename similar to get(), it is needed to use cas()
    time_last = time.time()
    page = database.Page(pagename = pagename, content = content)        
    page.put()
    client.cas(pagename, (page, time_last))    #This method makes sure that each time only one user can write to the cache under the same name.

    return (page, time_last) 