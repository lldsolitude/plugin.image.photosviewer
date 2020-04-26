# -*- coding: utf-8 -*-

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
except:
    from pysqlite2 import dbapi2 as sqlite

import xbmc

class DB(object):

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

    def GetMomentList(self, year, month):
        moment_list = []
        cur = self.dbconn.cursor()
        try:
            if year is None:
                cur.execute("""SELECT strftime('%Y', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') as y
                               FROM ZGENERICASSET a, ZADDITIONALASSETATTRIBUTES b
                               WHERE b.ZASSET = a.Z_PK
                                 AND a.ZCLOUDDELETESTATE = 0
                                 AND a.ZCOMPLETE = 1
                                 AND a.ZHIDDEN = 0
                                 AND a.ZTRASHEDSTATE = 0
                               GROUP BY y
                               ORDER BY y DESC
                               """)
            elif month is None:
                cur.execute("""SELECT strftime('%m', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') as m
                               FROM ZGENERICASSET a, ZADDITIONALASSETATTRIBUTES b
                               WHERE b.ZASSET = a.Z_PK
                                 AND a.ZCLOUDDELETESTATE = 0
                                 AND a.ZCOMPLETE = 1
                                 AND a.ZHIDDEN = 0
                                 AND a.ZTRASHEDSTATE = 0
                                 AND strftime('%Y', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY m
                               ORDER BY m ASC
                               """, ('%s' % (year[0]),))
            else:
                cur.execute("""SELECT strftime('%d', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') as d
                               FROM ZGENERICASSET a, ZADDITIONALASSETATTRIBUTES b
                               WHERE b.ZASSET = a.Z_PK
                                 AND a.ZCLOUDDELETESTATE = 0
                                 AND a.ZCOMPLETE = 1
                                 AND a.ZHIDDEN = 0
                                 AND a.ZTRASHEDSTATE = 0
                                 AND strftime('%Y-%m', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY d
                               ORDER BY d ASC
                               """, ('%s-%s' % (year[0], month[0]),))
            for row in cur:
                moment_list.append(row)
        except Exception as e:
            xbmc.log("photosviewer.db: GetMomentList: " + e, xbmc.LOGERROR)
        cur.close()
        return moment_list

    def GetFolderList(self, folderUuid):
        folder_list = []
        cur = self.dbconn.cursor()
        try:
            if folderUuid == 'root':
                cur.execute("""SELECT f.ZTITLE, f.ZUUID
                               FROM ZGENERICALBUM f, ZGENERICALBUM p
                               WHERE f.ZCLOUDDELETESTATE = 0
                                 AND f.ZTRASHEDSTATE = 0
                                 AND f.ZKIND = 4000
                                 AND f.ZPARENTFOLDER = p.Z_PK
                                 AND p.ZKIND = 3999
                               ORDER BY f.ZTITLE ASC""")
            else:
                cur.execute("""SELECT f.ZTITLE, f.ZUUID
                               FROM ZGENERICALBUM f, ZGENERICALBUM p
                               WHERE f.ZCLOUDDELETESTATE = 0
                                 AND f.ZTRASHEDSTATE = 0
                                 AND f.ZKIND = 4000
                                 AND f.ZPARENTFOLDER = p.Z_PK
                                 AND p.ZUUID = ?
                               ORDER BY f.ZTITLE ASC""", (folderUuid,))
            for row in cur:
                folder_list.append(row)
        except Exception as e:
            xbmc.log("photoapp.db: GetFolderList: " + e, xbmc.LOGERROR)
        cur.close()
        return folder_list

    def GetAlbumList(self, folderUuid):
        album_list = []
        cur = self.dbconn.cursor()
        try:
            if folderUuid == 'root':
                cur.execute("""SELECT a.ZTITLE, a.ZUUID
                               FROM ZGENERICALBUM a, ZGENERICALBUM f
                               WHERE a.ZCLOUDDELETESTATE = 0
                                 AND a.ZTRASHEDSTATE = 0
                                 AND a.ZKIND = 2
                                 AND a.ZPARENTFOLDER = f.Z_PK
                                 AND f.ZKIND = 3999
                               ORDER BY a.ZTITLE ASC""")
            else:
                cur.execute("""SELECT a.ZTITLE, a.ZUUID
                               FROM ZGENERICALBUM a, ZGENERICALBUM f
                               WHERE a.ZCLOUDDELETESTATE = 0
                                 AND a.ZTRASHEDSTATE = 0
                                 AND a.ZKIND = 2
                                 AND a.ZPARENTFOLDER = f.Z_PK
                                 AND f.ZUUID = ?
                               ORDER BY a.ZTITLE ASC""", (folderUuid,))
            for row in cur:
                album_list.append(row)
        except Exception as e:
            xbmc.log("photoapp.db: GetAlbumList: " + e, xbmc.LOGERROR)
        cur.close()
        return album_list

    def GetSlideshowList(self):
        slideshow_list = []
        cur = self.dbconn.cursor()
        try:
            cur.execute("""SELECT a.ZTITLE, a.ZUUID
                           FROM ZGENERICALBUM a, ZGENERICALBUM f
                           WHERE a.ZCLOUDDELETESTATE = 0
                             AND a.ZTRASHEDSTATE = 0
                             AND a.ZKIND = 1508
                             AND a.ZPARENTFOLDER = f.Z_PK
                             AND f.ZKIND = 3998
                           ORDER BY a.ZTITLE ASC""")
            for row in cur:
                slideshow_list.append(row)
        except Exception as e:
            xbmc.log("photoapp.db: GetSlideshowList: " + e, xbmc.LOGERROR)
        cur.close()
        return slideshow_list

    def GetVideoList(self):
        video_list = []
        cur = self.dbconn.cursor()
        try:
            cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                           FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                           WHERE m.ZCLOUDDELETESTATE = 0
                             AND m.ZCOMPLETE = 1
                             AND m.ZHIDDEN = 0
                             AND m.ZTRASHEDSTATE = 0
                             AND m.ZKIND = 1
                             AND b.ZASSET = m.Z_PK
                           ORDER BY m.ZDATECREATED ASC""")
            for row in cur:
                video_list.append(row)
        except Exception as e:
            xbmc.log("photoapp.db: GetVideoList: " + e, xbmc.LOGERROR)
        cur.close()
        return video_list

    def GetPictureList(self, uuid, action):
        picture_list = []
        cur = self.dbconn.cursor()
        try:
            if action == 'moments':
                cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                               FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                               WHERE m.ZCLOUDDELETESTATE = 0
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND m.ZUUID = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", (uuid,))
            elif action == 'search_by_year':
                (year) = uuid
                cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                               FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                               WHERE m.ZCLOUDDELETESTATE = 0
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND strftime('%Y', m.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", ('%s' % (year),))
            elif action == 'search_by_month':
                (year, month) = uuid
                cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                               FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                               WHERE m.ZCLOUDDELETESTATE = 0
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND strftime('%Y-%m', m.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", ('%s-%s' % (year, month),))
            elif action == 'search_by_day':
                (year, month, day) = uuid
                cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                               FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                               WHERE m.ZCLOUDDELETESTATE = 0
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND strftime('%Y-%m-%d', m.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", ('%s-%s-%s' % (year, month, day),))
            elif action == 'search_by_timestamp':
                (timestamp) = uuid
                cur1 = self.dbconn.cursor()
                cur1.execute("""SELECT strftime('%Y-%m-%d', ? + 978307200, 'unixepoch')""", ('%d' % (int(float(timestamp))),))
                (date) = cur1.fetchone()
                cur1.close()
                cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                               FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                               WHERE m.ZCLOUDDELETESTATE = 0
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND strftime('%Y-%m-%d', m.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", (date[0],))
            else:
                cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                               FROM ZGENERICASSET m, Z_26ASSETS l, ZGENERICALBUM a, ZADDITIONALASSETATTRIBUTES b
                               WHERE l.Z_26ALBUMS = a.Z_PK
                                 AND m.Z_PK = l.Z_34ASSETS
                                 AND m.ZCLOUDDELETESTATE = 0
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND a.ZUUID = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", (uuid,))
            for row in cur:
                picture_list.append(row)
        except Exception as e:
            xbmc.log("photoapp.db: GetPictureList: " + e, xbmc.LOGERROR)
        cur.close()
        return picture_list
