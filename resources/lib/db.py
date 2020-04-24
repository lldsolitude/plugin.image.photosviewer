# -*- coding: utf-8 -*-

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os
import time
import locale

import xbmc
from common import *

class DB:

    def __init__(self, dbfile):
        self.OpenDB(dbfile)

    def __del__(self):
        self.CloseDB()

    def OpenDB(self, dbfile):
        try:
            self.dbconn = sqlite.connect(dbfile)
        except Exception, e:
            pass

    def CloseDB(self):
        try:
            self.dbconn.close()
        except Exception, e:
            pass

    def GetMomentList(self, year, month):
        moment_list = []
        cur = self.dbconn.cursor()
        try:
            if year is None:
                cur.execute("""SELECT strftime('%Y', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') as y
                               FROM ZGENERICASSET a, ZADDITIONALASSETATTRIBUTES b
                               WHERE b.ZASSET = a.Z_PK
                               GROUP BY y
                               ORDER BY y DESC
                               """)
            elif month is None:
                cur.execute("""SELECT strftime('%m', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') as m
                               FROM ZGENERICASSET a, ZADDITIONALASSETATTRIBUTES b
                               WHERE b.ZASSET = a.Z_PK
                                 AND strftime('%Y', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY m
                               ORDER BY m ASC
                               """, ('%s' % (year[0]),))
            else:
                cur.execute("""SELECT strftime('%d', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') as d
                               FROM ZGENERICASSET a, ZADDITIONALASSETATTRIBUTES b
                               WHERE b.ZASSET = a.Z_PK
                                 AND strftime('%Y-%m', a.ZDATECREATED+b.ZTIMEZONEOFFSET+978307200, 'unixepoch') = ?
                               GROUP BY d
                               ORDER BY d ASC
                               """, ('%s-%s' % (year[0], month[0]),))
            for row in cur:
                moment_list.append(row)
        except Exception, e:
            print "photoapp.db: GetMomentList: " + smart_utf8(e)
            pass
        cur.close()
        return moment_list

    def GetFolderList(self, folderUuid):
        folder_list = []
        cur = self.dbconn.cursor()
        try:
            cur.execute("""SELECT f.ZTITLE, f.ZCLOUDGUID
                           FROM ZGENERICALBUM f, ZGENERICALBUM p
                           WHERE f.ZCLOUDDELETESTATE = 0
                             AND f.ZCLOUDLOCALSTATE = 1
                             AND f.ZTRASHEDSTATE = 0
                             AND f.ZKIND = 4000
                             AND f.ZPARENTFOLDER = p.Z_PK
                             AND p.ZCLOUDGUID = ?
                           ORDER BY f.ZTITLE ASC""", (folderUuid,))
            for row in cur:
                folder_list.append(row)
        except Exception, e:
            print "photoapp.db: GetFolderList: " + smart_utf8(e)
            pass
        cur.close()
        return folder_list

    def GetAlbumList(self, folderUuid):
        album_list = []
        cur = self.dbconn.cursor()
        try:
            cur.execute("""SELECT a.ZTITLE, a.ZCLOUDGUID
                           FROM ZGENERICALBUM a, ZGENERICALBUM f
                           WHERE a.ZCLOUDDELETESTATE = 0
                             AND a.ZCLOUDLOCALSTATE = 1
                             AND a.ZTRASHEDSTATE = 0
                             AND a.ZKIND = 2
                             AND a.ZPARENTFOLDER = f.Z_PK
                             AND f.ZCLOUDGUID = ?
                           ORDER BY a.ZTITLE DESC""", (folderUuid,))
            for row in cur:
                album_list.append(row)
        except Exception, e:
            print "photoapp.db: GetAlbumList: " + smart_utf8(e)
            pass
        cur.close()
        return album_list

    def GetVideoList(self):
        video_list = []
        cur = self.dbconn.cursor()
        try:
            cur.execute("""SELECT (m.ZDATECREATED+b.ZTIMEZONEOFFSET) as t, m.ZDIRECTORY, m.ZFILENAME, m.ZHASADJUSTMENTS
                           FROM ZGENERICASSET m, ZADDITIONALASSETATTRIBUTES b
                           WHERE m.ZCLOUDDELETESTATE = 0
                             AND m.ZCLOUDLOCALSTATE = 1
                             AND m.ZCOMPLETE = 1
                             AND m.ZHIDDEN = 0
                             AND m.ZTRASHEDSTATE = 0
                             AND m.ZKIND = 1
                             AND b.ZASSET = m.Z_PK
                           ORDER BY m.ZDATECREATED ASC""")
            for row in cur:
                video_list.append(row)
        except Exception, e:
            print "photoapp.db: GetVideoList: " + smart_utf8(e)
            pass
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
                                 AND m.ZCLOUDLOCALSTATE = 1
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
                                 AND m.ZCLOUDLOCALSTATE = 1
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
                                 AND m.ZCLOUDLOCALSTATE = 1
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
                                 AND m.ZCLOUDLOCALSTATE = 1
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
                                 AND m.ZCLOUDLOCALSTATE = 1
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
                                 AND m.ZCLOUDLOCALSTATE = 1
                                 AND m.ZCOMPLETE = 1
                                 AND m.ZHIDDEN = 0
                                 AND m.ZTRASHEDSTATE = 0
                                 AND b.ZASSET = m.Z_PK
                                 AND a.ZCLOUDGUID = ?
                               GROUP BY m.ZUUID
                               ORDER BY m.ZDATECREATED ASC""", (uuid,))
            for row in cur:
                picture_list.append(row)
        except Exception, e:
            print "photoapp.db: GetPictureList: " + smart_utf8(e)
            pass
        cur.close()
        return picture_list
