# -*- coding: utf-8 -*-

import datetime, time
import xbmc

def log_notice(msg=''):
    xbmc.log(smart_utf8(msg), xbmc.LOGNOTICE)

def log_error(msg=''):
    xbmc.log(smart_utf8(msg), xbmc.LOGERROR)

def notify(msg=''):
    xbmc.executebuiltin('XBMC.Notification(%s,%s,3000)' % ('Photos Viewer', smart_utf8(msg)))

def smart_unicode(s):
    """credit : sfaxman"""
    if not s:
    	return ''
    try:
    	if not isinstance(s, basestring):
    	    if hasattr(s, '__unicode__'):
    		s = unicode(s)
    	    else:
    		s = unicode(str(s), 'UTF-8')
    	elif not isinstance(s, unicode):
    	    s = unicode(s, 'UTF-8')
    except:
    	if not isinstance(s, basestring):
    	    if hasattr(s, '__unicode__'):
    		s = unicode(s)
    	    else:
    		s = unicode(str(s), 'ISO-8859-1')
    	elif not isinstance(s, unicode):
    	    s = unicode(s, 'ISO-8859-1')
    return s

def smart_utf8(s):
    return smart_unicode(s).encode('utf-8')
