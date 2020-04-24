# -*- coding: utf-8 -*-

import sys
import time
import os
import glob
import urllib
import urlparse
import datetime

import xbmc
import xbmcgui as gui
import xbmcplugin as plugin
import xbmcaddon
import xbmcvfs

from resources.lib.common import *
from resources.lib.db import *

addon = xbmcaddon.Addon()

plugin_path = addon.getAddonInfo("path")
resource_path = os.path.join(plugin_path, "resources")
lib_path = os.path.join(resource_path, "lib")
sys.path.append(lib_path)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

ICONS_PATH = os.path.join(resource_path, "icons")
ICON_FOLDER = ICONS_PATH+"/folder.png"
ICON_ALBUMS = ICONS_PATH+"/albums.png"

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def convert_timestamp(year=None, month=None, day=None, hour=None, minute=None, timestamp=None):
    if timestamp:
        # Use utcfromtimestamp because timestamp already has timezone offset.
        t = datetime.datetime.utcfromtimestamp(int(timestamp)+978307200)
        (year,month,day,hour,minute) = t.replace(year=t.year).strftime('%Y,%m,%d,%H,%M').split(',')
    if year:
        if month:
            m = addon.getLocalizedString(30017).split(',')
            mindex = int(month)-1
            if day:
                d = addon.getLocalizedString(30018).split(',')
                dindex = datetime.date(int(year), int(month), int(day)).weekday()
                if hour and minute:
                    itemname = addon.getLocalizedString(30030).format(year=year, month=m[mindex], day=day, day7=d[dindex], hour=hour, minute=minute)
                else:
                    itemname = addon.getLocalizedString(30031).format(year=year, month=m[mindex], day=day, day7=d[dindex])
                if dindex == 6:
                    itemname = '[COLOR red]' + itemname + '[/COLOR]'
                elif dindex == 5:
                    itemname = '[COLOR blue]' + itemname + '[/COLOR]'
            else:
                itemname = addon.getLocalizedString(30032).format(year=year, month=m[mindex])
        else:
            itemname = addon.getLocalizedString(30033).format(year=year)
    else:
        itemname = ''
    return itemname

class App:

    def __init__(self):

        self.params = {}
        qs = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query, keep_blank_values=True)
        for key in qs.keys():
            self.params[key] = qs[key][0]

        self.photo_app_path = addon.getSetting('photo_library_path')
        if self.photo_app_path == '':
            self.photo_app_path = os.path.join(os.getenv('HOME'), 'Pictures', addon.getLocalizedString(30000))
        addon.setSetting('photo_library_path', self.photo_app_path)

        self.photo_app_db_file = os.path.join(xbmc.translatePath(addon.getAddonInfo('Profile')), 'Photos.sqlite')
        self.photo_app_db_shm_file = os.path.join(xbmc.translatePath(addon.getAddonInfo('Profile')), 'Photos.sqlite-shm')
        self.photo_app_db_wal_file = os.path.join(xbmc.translatePath(addon.getAddonInfo('Profile')), 'Photos.sqlite-wal')
        self.photo_app_db_orig = os.path.join(self.photo_app_path, 'database', 'Photos.sqlite')
        self.photo_app_db_shm_orig = os.path.join(self.photo_app_path, 'database', 'Photos.sqlite-shm')
        self.photo_app_db_wal_orig = os.path.join(self.photo_app_path, 'database', 'Photos.sqlite-wal')
        if xbmcvfs.exists(self.photo_app_db_wal_orig):
            ctime = os.stat(self.photo_app_db_wal_orig).st_ctime
            mtime = os.stat(self.photo_app_db_wal_orig).st_mtime
            if xbmcvfs.exists(self.photo_app_db_wal_file) and os.stat(self.photo_app_db_wal_file).st_mtime == mtime:
                pass
            else:
                xbmcvfs.copy(self.photo_app_db_orig, self.photo_app_db_file)
                os.utime(self.photo_app_db_file, (ctime, mtime))
                xbmcvfs.copy(self.photo_app_db_shm_orig, self.photo_app_db_shm_file)
                os.utime(self.photo_app_db_shm_file, (ctime, mtime))
                xbmcvfs.copy(self.photo_app_db_wal_orig, self.photo_app_db_wal_file)
                os.utime(self.photo_app_db_wal_file, (ctime, mtime))
        else:
            ctime = os.stat(self.photo_app_db_orig).st_ctime
            mtime = os.stat(self.photo_app_db_orig).st_mtime
            if not xbmcvfs.exists(self.photo_app_db_wal_file) and xbmcvfs.exists(self.photo_app_db_file) and os.stat(self.photo_app_db_file).st_mtime == mtime:
                pass
            else:
                xbmcvfs.copy(self.photo_app_db_orig, self.photo_app_db_file)
                os.utime(self.photo_app_db_file, (ctime, mtime))

        self.photo_app_picture_path = os.path.join(self.photo_app_path, 'originals')
        self.photo_app_rendered_path = os.path.join(self.photo_app_path, 'resources', 'renders')
        # DB
        self.db = None

    def open_db(self):
        if self.db is not None: return
        try:
            self.db = DB(self.photo_app_db_file)
        except:
            pass

    def close_db(self):
        try:
            self.db.CloseDB()
        except:
            pass

    def list_moments(self, year, month):
        n = 0
        moments = self.db.GetMomentList(year, month)
        for (name,) in moments:
            if year is None:
                url = build_url({'action': 'moments', 'year': name})
                item = gui.ListItem(convert_timestamp(year=name), iconImage='DefaultYear.png', thumbnailImage='DefaultYear.png')
                contextmenu = []
                contextmenu.append((addon.getLocalizedString(30012).format(period=convert_timestamp(year=name)), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_year', 'year': name})))
                item.addContextMenuItems(contextmenu, replaceItems=True)
            elif month is None:
                url = build_url({'action': 'moments', 'year': year[0], 'month': name})
                item = gui.ListItem(convert_timestamp(year=year[0],month=name), iconImage='DefaultYear.png', thumbnailImage='DefaultYear.png')
                contextmenu = []
                contextmenu.append((addon.getLocalizedString(30012).format(period=convert_timestamp(year=year[0],month=name)), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_month', 'year': year[0], 'month': name})))
                contextmenu.append((addon.getLocalizedString(30012).format(period=convert_timestamp(year=year[0])), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_year', 'year': year[0]})))
                item.addContextMenuItems(contextmenu, replaceItems=True)
            else:
                url = build_url({'action': 'search_by_day', 'year': year[0], 'month': month[0], 'day': name})
                item = gui.ListItem(convert_timestamp(year=year[0],month=month[0],day=name), iconImage='DefaultYear.png', thumbnailImage='DefaultYear.png')
                contextmenu = []
                contextmenu.append((addon.getLocalizedString(30012).format(period=convert_timestamp(year=year[0],month=month[0])), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_month', 'year': year[0], 'month': month[0]})))
                contextmenu.append((addon.getLocalizedString(30012).format(period=convert_timestamp(year=year[0])), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_year', 'year': year[0]})))
                item.addContextMenuItems(contextmenu, replaceItems=True)
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        return n

    def list_albums(self, folderUuid):
        n = 0
        folders = self.db.GetFolderList(folderUuid)
        for (name, uuid) in folders:
            url = build_url({'action': 'albums', 'folderUuid': uuid})
            item = gui.ListItem(name, iconImage=ICON_FOLDER, thumbnailImage=ICON_FOLDER)
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        albums = self.db.GetAlbumList(folderUuid)
        for (name, uuid) in albums:
            url = build_url({'action': 'albums', 'uuid': uuid})
            item = gui.ListItem(name, iconImage=ICON_ALBUMS, thumbnailImage=ICON_ALBUMS)
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        return n

    def list_photos(self, uuid, action):
        pictures = self.db.GetPictureList(uuid, action)
        n = 0
        for (imageDate, imagePath, imageFilename, isAdjusted) in pictures:
            if isAdjusted == 0:
                imagePath = os.path.join(self.photo_app_picture_path, imagePath, imageFilename)
            else:
                imagePath = os.path.join(self.photo_app_rendered_path, imagePath, re.sub('^([-A-Z0-9]*)\.', '\g<1>_1_201_a.', imageFilename))
            item = gui.ListItem(convert_timestamp(timestamp=imageDate), iconImage=imagePath, thumbnailImage=imagePath)
            contextmenu = []
            contextmenu.append((addon.getLocalizedString(30010), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_timestamp', 'timestamp': imageDate})))
            contextmenu.append((addon.getLocalizedString(30014), 'XBMC.Container.Update(%s)' % build_url({})))
            item.addContextMenuItems(contextmenu, replaceItems=True)
            plugin.addDirectoryItem(addon_handle, imagePath, item, False)
            n += 1
        return n

    def list_videos(self):
        n = 0
        videos = self.db.GetVideoList()
        for (imageDate, imagePath, imageFilename) in videos:
            if isAdjusted == 0:
                imagePath = os.path.join(self.photo_app_picture_path, imagePath, imageFilename)
            else:
                imagePath = os.path.join(self.photo_app_rendered_path, imagePath, re.sub('^([-A-Z0-9]*)\.', '\g<1>_2_0_a.', imageFilename))
            item = gui.ListItem(convert_timestamp(timestamp=imageDate), iconImage=imagePath, thumbnailImage=imagePath)
            contextmenu = []
            contextmenu.append((addon.getLocalizedString(30010), 'XBMC.Container.Update(%s)' % build_url({'action': 'search_by_timestamp', 'timestamp': imageDate})))
            contextmenu.append((addon.getLocalizedString(30014), 'XBMC.Container.Update(%s)' % build_url({})))
            item.addContextMenuItems(contextmenu, replaceItems=True)
            plugin.addDirectoryItem(addon_handle, imagePath, item, False)
            n += 1
        return n

    def main_menu(self):
        url = build_url({'action': 'moments'})
        item = gui.ListItem(addon.getLocalizedString(30001), iconImage='DefaultPicture.png', thumbnailImage='DefaultPicture.png')
        plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'videos'})
        item = gui.ListItem(addon.getLocalizedString(30005), iconImage='DefaultVideo.png', thumbnailImage='DefaultVideo.png')
        plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'albums', 'folderUuid': '----Root-Folder----'})
        item = gui.ListItem(addon.getLocalizedString(30004), iconImage='DefaultFolder.png', thumbnailImage='DefaultFolder.png')
        plugin.addDirectoryItem(addon_handle, url, item, True)

        return 4

if __name__ == '__main__':

    action_result = None
    items = 0

    log_notice('argv[0] = %s' % sys.argv[0])
    log_notice('argv[1] = %s' % sys.argv[1])
    log_notice('argv[2] = %s' % sys.argv[2])

    action = args.get('action', None)
    folderUuid = args.get('folderUuid', None)
    uuid = args.get('uuid', None)
    year = args.get('year', None)
    month = args.get('month', None)
    day = args.get('day', None)

    timestamp = args.get('timestamp', None)

    app = App()
    app.open_db()

    if action is None:
        items = app.main_menu()
    elif not (uuid is None):
        items = app.list_photos(uuid[0], action[0])
    elif action[0] == 'moments':
        items = app.list_moments(year, month)
    elif action[0] == 'videos':
        items = app.list_videos()
    elif action[0] == 'albums':
        items = app.list_albums(folderUuid[0])

    elif action[0] == 'search_by_year':
        items = app.list_photos((year[0]), action[0])
        mode = 'thumbnail'
    elif action[0] == 'search_by_month':
        items = app.list_photos((year[0], month[0]), action[0])
        mode = 'thumbnail'
    elif action[0] == 'search_by_day':
        items = app.list_photos((year[0], month[0], day[0]), action[0])
        mode = 'thumbnail'
    elif action[0] == 'search_by_timestamp':
        items = app.list_photos((timestamp[0]), action[0])
        mode = 'thumbnail'

    app.close_db()

    if items == 0:
        action_result = addon.getLocalizedString(30100)
    else:
        plugin.endOfDirectory(addon_handle, True)

    xbmc.sleep(300)
    if action_result: notify(action_result)
