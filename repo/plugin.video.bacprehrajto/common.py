import os

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs

from model.QS import QS

_ADDON_ID = 'plugin.video.bacprehrajto'
addon = xbmcaddon.Addon(id=_ADDON_ID)

### SETTINGS
g_is_debug_logs_enabled = True if addon.getSetting("is_debug_logs_enabled") == 'true' else False
g_max_searched_vids = int(addon.getSetting("ls"))
g_max_duplicities = int(addon.getSetting("max_duplicities"))
g_truncate_titles = True if addon.getSetting("truncate_titles") == 'true' else False
g_download_path = addon.getSetting("download")
qss = addon.getSetting("quality_selector")
g_quality_selector: QS = QS.Selector
if qss == 'Max':
    g_quality_selector = QS.Max
elif qss == 'Komprimovaná':
    g_quality_selector = QS.BestCompressed
elif qss == 'Vybrat':
    g_quality_selector = QS.Selector

### PATHs
translated_path = xbmcvfs.translatePath('special://home/addons/' + _ADDON_ID)
history_path = os.path.join(translated_path,'resources', 'history.txt')
subtitles_path = os.path.join(translated_path,'resources', 'subtitles/')
images_path = os.path.join(translated_path,'resources', 'images/')
quality_icons_path = os.path.join(translated_path,'resources', 'images/quality/')
cache_path = os.path.join(translated_path,'resources', 'cache/')
qr_path = os.path.join(translated_path,'resources', 'qr.png')

headers = {'user-agent': 'kodi/prehraj.to'}
