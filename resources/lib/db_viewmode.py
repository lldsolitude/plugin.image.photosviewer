from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object
try:
    from sqlite3 import dbapi2 as sqlite
except Exception:
    from pysqlite2 import dbapi2 as sqlite

import xbmc

class ViewModeDB(object):

    def __init__(self, dbfile):
        self.OpenDB(dbfile)

    def __del__(self):
        self.CloseDB()

    def OpenDB(self, dbfile):
        try:
            self.dbconn = sqlite.connect(dbfile)
        except Exception:
            pass

    def CloseDB(self):
        try:
            self.dbconn.close()
        except Exception:
            pass

    def GetViewMode(self, url_current):
        mode_list = []
        cur = self.dbconn.cursor()
        try:
            cur.execute("""SELECT path FROM view WHERE path = ?""", (url_current,))
            for row in cur:
                mode_list.append(row)
        except Exception as e:
            xbmc.log('photosviewer.viewmode_db: GetViewMode: ' + e, xbmc.LOGERROR)
        cur.close()
        return mode_list
