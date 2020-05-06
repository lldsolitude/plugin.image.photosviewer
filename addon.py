from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object
import sys
import os
import urllib.request, urllib.parse, urllib.error
import datetime
import re

import xbmc
import xbmcgui as gui
import xbmcplugin as plugin
import xbmcaddon
import xbmcvfs

from resources.lib.db import *
from resources.lib.db_viewmode import *

addon = xbmcaddon.Addon()

plugin_path = addon.getAddonInfo('path').decode('utf-8')
resource_path = os.path.join(plugin_path, 'resources')
lib_path = os.path.join(resource_path, 'lib')
sys.path.append(lib_path)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def convert_timestamp(year=None, month=None, day=None,
                      hour=None, minute=None, timestamp=None):
    if timestamp:
        # Use utcfromtimestamp because timestamp already has timezone offset.
        t = datetime.datetime.utcfromtimestamp(int(timestamp) + 978307200)
        (year, month, day, hour, minute) = t.replace(year=t.year).strftime('%Y,%m,%d,%H,%M').split(',')
    if year:
        if month:
            m = addon.getLocalizedString(30017).split(',')
            mindex = int(month) - 1
            if day:
                d = addon.getLocalizedString(30018).split(',')
                dindex = datetime.date(int(year), int(month), int(day)).weekday()
                if hour and minute:
                    itemname = addon.getLocalizedString(30030).format(year=year, month=m[mindex],
                                                                      day=day, day7=d[dindex],
                                                                      hour=hour, minute=minute)
                else:
                    itemname = addon.getLocalizedString(30031).format(year=year, month=m[mindex],
                                                                      day=day, day7=d[dindex])
                if dindex == 5 or dindex == 6:
                    itemname = '[COLOR blue]' + itemname + '[/COLOR]'
            else:
                itemname = addon.getLocalizedString(30032).format(year=year, month=m[mindex])
        else:
            itemname = addon.getLocalizedString(30033).format(year=year)
    else:
        itemname = ''
    return itemname

class App(object):

    def __init__(self):

        self.params = {}
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query, keep_blank_values=True)
        for key in list(qs.keys()):
            self.params[key] = qs[key][0]

        self.photo_app_path = addon.getSetting('photo_library_path').decode('utf-8')
        if self.photo_app_path == '':
            self.photo_app_path = os.path.join(
                os.getenv('HOME'), 'Pictures', addon.getLocalizedString(30000))
        addon.setSetting('photo_library_path', self.photo_app_path)
        self.display_adjusted = addon.getSetting('display_adjusted')

        self.photo_app_db_file = os.path.join(
            xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8')), 'Photos.sqlite')
        self.photo_app_db_wal_file = os.path.join(
            xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8')), 'Photos.sqlite-wal')
        self.photo_app_db_orig = os.path.join(
            self.photo_app_path, 'database', 'Photos.sqlite')
        self.photo_app_db_wal_orig = os.path.join(
            self.photo_app_path, 'database', 'Photos.sqlite-wal')
        ctime = os.stat(self.photo_app_db_orig).st_ctime
        mtime = os.stat(self.photo_app_db_orig).st_mtime
        if xbmcvfs.exists(self.photo_app_db_wal_orig):
            ctime_wal = os.stat(self.photo_app_db_wal_orig).st_ctime
            mtime_wal = os.stat(self.photo_app_db_wal_orig).st_mtime
            if (xbmcvfs.exists(self.photo_app_db_file)
                    and os.stat(self.photo_app_db_file).st_mtime >= mtime_wal):
                pass
            else:
                xbmcvfs.copy(self.photo_app_db_orig, self.photo_app_db_file)
                os.utime(self.photo_app_db_file, (ctime, mtime))
                xbmcvfs.copy(self.photo_app_db_wal_orig, self.photo_app_db_wal_file)
                os.utime(self.photo_app_db_wal_file, (ctime_wal, mtime_wal))
        else:
            if (xbmcvfs.exists(self.photo_app_db_file)
                    and os.stat(self.photo_app_db_file).st_mtime >= mtime):
                pass
            else:
                xbmcvfs.copy(self.photo_app_db_orig, self.photo_app_db_file)
                os.utime(self.photo_app_db_file, (ctime, mtime))

        self.photo_app_picture_path = os.path.join(self.photo_app_path, 'originals')
        self.photo_app_rendered_path = os.path.join(self.photo_app_path, 'resources', 'renders')

        self.viewmode_db_file = os.path.join(xbmc.translatePath('special://database'), 'ViewModes6.db')

        self.db = None
        self.viewmode_db = None
        self.view_mode = 0

    def open_db(self):
        if self.db is not None: return
        try:
            self.db = DB(self.photo_app_db_file)
        except Exception:
            pass

    def close_db(self):
        try:
            self.db.CloseDB()
        except Exception:
            pass

    def open_viewmode_db(self):
        if self.viewmode_db is not None: return
        try:
            self.viewmode_db = ViewModeDB(self.viewmode_db_file)
        except Exception:
            pass

    def close_viewmode_db(self):
        try:
            self.viewmode_db.CloseDB()
        except Exception:
            pass

    def set_viewmode(self):
        view_mode = int(addon.getSetting('view_mode'))
        if (view_mode == 1):
            self.view_mode = 500    # Wall
        elif (view_mode == 2):
            self.view_mode = 53     # Shift
        elif (view_mode == 3):
            self.view_mode = 54     # InfoWall
        else:
            self.view_mode = 55     # WideList

    def list_moments(self, year, month, url_current):
        n = 0
        moments = self.db.GetMomentList(year, month)
        for (name,) in moments:
            if year is None:
                url = build_url({'action': 'moments', 'year': name})
                item = gui.ListItem(convert_timestamp(year=name))
                item.setArt({'icon': 'DefaultYear.png', 'thumb': 'DefaultYear.png'})
                contextmenu = []
                contextmenu.append((
                    addon.getLocalizedString(30012).format(
                        period=convert_timestamp(year=name)),
                    'XBMC.Container.Update(%s)' % build_url(
                        {'action': 'search_by_year', 'year': name})))
                item.addContextMenuItems(contextmenu)
            elif month is None:
                url = build_url({'action': 'moments', 'year': year[0], 'month': name})
                item = gui.ListItem(convert_timestamp(year=year[0], month=name))
                item.setArt({'icon': 'DefaultYear.png', 'thumb': 'DefaultYear.png'})
                contextmenu = []
                contextmenu.append((
                    addon.getLocalizedString(30012).format(
                        period=convert_timestamp(year=year[0],month=name)),
                    'XBMC.Container.Update(%s)' % build_url(
                        {'action': 'search_by_month', 'year': year[0], 'month': name})))
                contextmenu.append((
                    addon.getLocalizedString(30012).format(
                        period=convert_timestamp(year=year[0])),
                    'XBMC.Container.Update(%s)' % build_url(
                        {'action': 'search_by_year', 'year': year[0]})))
                item.addContextMenuItems(contextmenu)
            else:
                url = build_url({'action': 'search_by_day',
                                 'year': year[0], 'month': month[0], 'day': name})
                item = gui.ListItem(convert_timestamp(year=year[0],month=month[0],day=name))
                item.setArt({'icon': 'DefaultYear.png', 'thumb': 'DefaultYear.png'})
                contextmenu = []
                contextmenu.append((
                    addon.getLocalizedString(30012).format(
                        period=convert_timestamp(year=year[0],month=month[0])),
                    'XBMC.Container.Update(%s)' % build_url(
                        {'action': 'search_by_month', 'year': year[0], 'month': month[0]})))
                contextmenu.append((
                    addon.getLocalizedString(30012).format(
                        period=convert_timestamp(year=year[0])),
                    'XBMC.Container.Update(%s)' % build_url(
                        {'action': 'search_by_year', 'year': year[0]})))
                item.addContextMenuItems(contextmenu)
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        if not self.viewmode_db.GetViewMode(url_current):
            self.view_mode = 52    # IconWall
        return n

    def list_albums(self, folderUuid, url_current):
        n = 0
        folders = self.db.GetFolderList(folderUuid)
        for (name, uuid) in folders:
            url = build_url({'action': 'albums', 'folderUuid': uuid})
            item = gui.ListItem(name)
            item.setArt({'icon': 'DefaultFolder.png', 'thumb': 'DefaultFolder.png'})
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        albums = self.db.GetAlbumList(folderUuid)
        for (name, uuid) in albums:
            url = build_url({'action': 'albums', 'uuid': uuid})
            item = gui.ListItem(name)
            item.setArt({'icon': 'DefaultPicture.png', 'thumb': 'DefaultPicture.png'})
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        if not self.viewmode_db.GetViewMode(url_current):
            self.view_mode = 52    # IconWall
        return n

    def list_slideshows(self, url_current):
        n = 0
        slideshows = self.db.GetSlideshowList()
        for (name, uuid) in slideshows:
            url = build_url({'action': 'slideshows', 'uuid': uuid})
            item = gui.ListItem(name)
            item.setArt({'icon': 'DefaultPicture.png', 'thumb': 'DefaultPicture.png'})
            plugin.addDirectoryItem(addon_handle, url, item, True)
            n += 1
        if not self.viewmode_db.GetViewMode(url_current):
            self.view_mode = 52    # IconWall
        return n

    def list_photos(self, uuid, action, url_current):
        pictures = self.db.GetPictureList(uuid, action)
        n = 0
        for (imageDate, imagePath, imageFilename, isAdjusted) in pictures:
            if isAdjusted == 1 and self.display_adjusted == 'true':
                imagePath = os.path.join(
                    self.photo_app_rendered_path, imagePath,
                    re.sub(r'^([-A-Z0-9]*)\.', r'\g<1>_1_201_a.', imageFilename))
            else:
                imagePath = os.path.join(
                    self.photo_app_picture_path, imagePath, imageFilename)
            item = gui.ListItem(convert_timestamp(timestamp=imageDate))
            contextmenu = []
            contextmenu.append((
                addon.getLocalizedString(30010),
                'XBMC.Container.Update(%s)' % build_url(
                    {'action': 'search_by_timestamp', 'timestamp': imageDate})))
            contextmenu.append((
                addon.getLocalizedString(30014),
                'XBMC.Container.Update(%s)' % build_url({})))
            item.addContextMenuItems(contextmenu)
            plugin.addDirectoryItem(addon_handle, imagePath, item, False)
            n += 1
        plugin.setContent(addon_handle, 'images')
        if not self.viewmode_db.GetViewMode(url_current):
            self.set_viewmode()
        return n

    def list_videos(self, url_current):
        n = 0
        videos = self.db.GetVideoList()
        for (imageDate, imagePath, imageFilename, isAdjusted) in videos:
            if isAdjusted == 1 and self.display_adjusted == 'true':
                imagePath = os.path.join(
                    self.photo_app_rendered_path, imagePath,
                    re.sub(r'^([-A-Z0-9]*)\.', r'\g<1>_2_0_a.', imageFilename))
            else:
                imagePath = os.path.join(
                    self.photo_app_picture_path, imagePath, imageFilename)
            item = gui.ListItem(convert_timestamp(timestamp=imageDate))
            contextmenu = []
            contextmenu.append((
                addon.getLocalizedString(30010),
                'XBMC.Container.Update(%s)' % build_url(
                    {'action': 'search_by_timestamp', 'timestamp': imageDate})))
            contextmenu.append((
                addon.getLocalizedString(30014),
                'XBMC.Container.Update(%s)' % build_url({})))
            item.addContextMenuItems(contextmenu)
            plugin.addDirectoryItem(addon_handle, imagePath, item, False)
            n += 1
        plugin.setContent(addon_handle, 'videos')
        if not self.viewmode_db.GetViewMode(url_current):
            self.set_viewmode()
        return n

    def main_menu(self):
        url = build_url({'action': 'moments'})
        item = gui.ListItem(addon.getLocalizedString(30001))
        item.setArt({'icon': 'DefaultPicture.png', 'thumb': 'DefaultPicture.png'})
        plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'albums', 'folderUuid': 'root'})
        item = gui.ListItem(addon.getLocalizedString(30004))
        item.setArt({'icon': 'DefaultFolder.png', 'thumb': 'DefaultFolder.png'})
        plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'videos'})
        item = gui.ListItem(addon.getLocalizedString(30005))
        item.setArt({'icon': 'DefaultVideo.png', 'thumb': 'DefaultVideo.png'})
        plugin.addDirectoryItem(addon_handle, url, item, True)

        url = build_url({'action': 'slideshows'})
        item = gui.ListItem(addon.getLocalizedString(30006))
        item.setArt({'icon': 'DefaultFolder.png', 'thumb': 'DefaultFolder.png'})
        plugin.addDirectoryItem(addon_handle, url, item, True)

        self.view_mode = 55    # WideList

        return 4

if __name__ == '__main__':

    action_result = None
    items = 0

    url_current = sys.argv[0] + sys.argv[2]
    action = args.get('action', None)
    folderUuid = args.get('folderUuid', None)
    uuid = args.get('uuid', None)
    year = args.get('year', None)
    month = args.get('month', None)
    day = args.get('day', None)
    timestamp = args.get('timestamp', None)

    app = App()
    app.open_db()
    app.open_viewmode_db()

    if action is None:
        items = app.main_menu()
    elif not (uuid is None):
        items = app.list_photos(uuid[0], action[0], url_current)
    elif action[0] == 'moments':
        items = app.list_moments(year, month, url_current)
    elif action[0] == 'albums':
        items = app.list_albums(folderUuid[0], url_current)
    elif action[0] == 'videos':
        items = app.list_videos(url_current)
    elif action[0] == 'slideshows':
        items = app.list_slideshows(url_current)

    elif action[0] == 'search_by_year':
        items = app.list_photos((year[0]), action[0], url_current)
    elif action[0] == 'search_by_month':
        items = app.list_photos((year[0], month[0]), action[0], url_current)
    elif action[0] == 'search_by_day':
        items = app.list_photos((year[0], month[0], day[0]), action[0], url_current)
    elif action[0] == 'search_by_timestamp':
        items = app.list_photos((timestamp[0]), action[0], url_current)

    app.close_db()
    app.close_viewmode_db()

    if items == 0:
        action_result = addon.getLocalizedString(30100)
    else:
        plugin.endOfDirectory(addon_handle, True)
        xbmc.sleep(300)
        if app.view_mode:
            xbmc.executebuiltin('Container.SetViewMode(%d)' % app.view_mode)
    
    if action_result:
        xbmc.executebuiltin(b'XBMC.Notification(%s,%s,3000)' % (b'Photos Viewer', action_result.encode('utf-8')))
