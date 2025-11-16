# -*- coding: utf-8 -*-

import json
import os
import sys
import time
from typing import List, Optional, Tuple
from urllib.parse import parse_qsl, unquote
from urllib.parse import urlparse
from urllib.request import urlopen

import requests
import unicodedata
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from bs4 import BeautifulSoup

from common import _ADDON_ID, addon, g_max_searched_vids, g_download_path, g_quality_selector, \
    history_path, \
    headers, cache_path
from model.QS import QS
from model.StreamData import StreamData
from model.SubData import SubData
from modules.SplitSelectorDialog import search_variants_dialog
from providers.Prehrajto import Prehrajto
from tmdb.tmdb_router import tmdb_router
from unidecode.unidecode import unidecode
from utils.ClipboardUtils import ClipboardUtils
from utils.StrUtils import truncate_middle, find_pattern, find_pattern_groups, convert_size, \
    get_file_size_human_readable
from utils.TimeUtils import format_eta_and_finish
from utils.utils import notify_file_size, dprint, \
    urlencode, get_quality_icon

_url = sys.argv[0]
_handle = int(sys.argv[1])

_last_page_content = None

_provider = Prehrajto()


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def encode(string):
    line = unicodedata.normalize('NFKD', string)
    output = ''
    for c in line:
        if not unicodedata.combining(c):
            output += c
    return output


def get_premium():
    if addon.getSetting("email") != '':
        login = {"password": addon.getSetting("password"), "email": addon.getSetting("email"),
                 '_submit': 'Přihlásit+se', 'remember': 'on', '_do': 'login-loginForm-submit'}
        res = requests.post("https://prehraj.to/", login)
        soup = BeautifulSoup(res.content, "html.parser")
        title = soup.find('ul', {'class': 'header__links'})
        title = title.find('span', {'class': 'color-green'})
        if title is None:
            premium = 0
            cookies = res.cookies
            xbmcgui.Dialog().notification("Přehraj.to", "Premium účet neaktivní", xbmcgui.NOTIFICATION_INFO, 4000,
                                          sound=False)
        else:
            premium = 1
            cookies = res.cookies
            xbmcgui.Dialog().notification("Přehraj.to", "Premium: " + title.text, xbmcgui.NOTIFICATION_INFO, 4000,
                                          sound=False)
    else:
        premium = 0
        cookies = ''
    return premium, cookies


# def play_video(link):
#     data = urlparse(link)
#
#     dprint(f'play_video(): quality_selector: ' + quality_selector)
#
#     # Max Compressed
#     url = requests.get("https://prehraj.to" + data.path, headers=headers).content
#     file, sub = get_link(url)
#
#     notify_file_size(file)
#
#     listitem = xbmcgui.ListItem(path = file)
#     if sub != "":
#         subtitles = []
#         subtitles.append(sub)
#         listitem.setSubtitles(subtitles)
#
#     ############
#     # video_info = listitem.getInfo('video')
#     # video_info['plot'] = 'Stream size: '+file_size_str+'\r\n'+video_info.get('plot', '')
#     # listitem.setInfo('video', video_info)
#
#     xbmcplugin.setResolvedUrl(_handle, True, listitem)

def get_premium_link(link) -> Optional[str]:
    nlink = "https://prehraj.to" + urlparse(link).path + "?do=download"
    res = requests.get(nlink, headers=headers, allow_redirects=False)

    if not res.headers.keys().__contains__('Location') or res.headers['Location'] is None:
        dprint(f'get_premium_link():\n nlink: '+ nlink+
               '\nlink: '+ link +
               '\nLocation is None'
               )

    return res.headers['Location']

def play_video(link, force_selector=False, force_quality = None):
    dprint(
        f'play_video(): force_selector: ' + str(force_selector) +
           ', quality_selector = ' + str(g_quality_selector) +
            ', force_selector = ' + str(force_selector) +
            ', force_quality = ' + str(force_quality)
    )

    if force_quality == QS.Max or (g_quality_selector == QS.Max and force_selector == False):  # Premium.
        file = get_premium_link(link)
        dprint("play_video(): premium link: " + file)
        notify_file_size(file)
        listitem = xbmcgui.ListItem(path=file)
        # Subtitles skipped. Premium should have them inside the file.

        xbmcplugin.setResolvedUrl(_handle, True, listitem)
    else:
        res = requests.get(link, headers=headers, allow_redirects=True)
        content = res.content
        link = res.url

        streams: Optional[List[StreamData]]
        subs: Optional[List[SubData]]
        streams, subs = _provider.get_streams_data(content)
        if streams is None or len(streams) == 0:
            # Streams unavailable, but premium link might still be available.
            play_video(link, force_quality=QS.Max)
            return

        if g_quality_selector == QS.BestCompressed and force_selector == False:  # Max Compressed

            # Find the highest quality stream (compressed)
            file = streams[0].path
            notify_file_size(file)

            listitem = xbmcgui.ListItem(path=file)

            # Download subs so they are properly named for the streamed video.
            name_wo_ext: Optional[str] = None
            extension: Optional[str] = None
            name_wo_ext, extension = get_name_ext(file, content)

            sub_paths = download_subtitles(subs, name_wo_ext, True, cache_path)

            if sub_paths is not None:
                subtitles = [item for item in sub_paths]
                listitem.setSubtitles(subtitles)

            ############
            # video_info = listitem.getInfo('video')
            # video_info['plot'] = 'Stream size: '+file_size_str+'\r\n'+video_info.get('plot', '')
            # listitem.setInfo('video', video_info)

            xbmcplugin.setResolvedUrl(_handle, True, listitem)
        elif g_quality_selector == QS.Selector or force_selector:  # Selector
            selected_file, is_premium = open_stream_selector(streams)

            if selected_file is None:
                # Canceled.
                return

            notify_file_size(selected_file)

            dprint("SELECTED: " + str(is_premium))
            dprint("SELECTED: " + selected_file)

            listitem = xbmcgui.ListItem(path=selected_file)

            name_wo_ext, extension = get_name_ext(selected_file, content)

            sub_paths = download_subtitles(subs, name_wo_ext, True, cache_path)

            if sub_paths is not None:
                subtitles = [item for item in sub_paths]
                listitem.setSubtitles(subtitles)

            xbmcplugin.setResolvedUrl(_handle, True, listitem)


def create_premium_link(link) -> str:
    return "https://prehraj.to" + urlparse(link).path + "?do=download"

# Returns:
# str = file path
# bool = is_premium?
def open_stream_selector(streams) -> Tuple[Optional[str], bool]:
    # Open selector.
    list_items = []
    for stream in streams:
        item = xbmcgui.ListItem(label=stream.label, label2=stream.label2)
        icon = get_quality_icon(stream.quality)
        item.setArt({'thumb': icon})
        list_items.append(item)

    selected = xbmcgui.Dialog().select(
        heading="Vybrat kvalitu",
        list=list_items,
        useDetails=True,
    )

    if selected == -1:
        return None, False

    return streams[selected].path, selected == 0


def play_video_premium(link, cookies):
    link = "https://prehraj.to" + urlparse(link).path
    url = requests.get(link, cookies=cookies).content
    file, sub = _provider.get_streams_data(url)

    res = requests.get(link + "?do=download", cookies=cookies, headers=headers, allow_redirects=False)
    file = res.headers['Location']

    notify_file_size(file)

    listitem = xbmcgui.ListItem(path=file)
    if sub != "":
        subtitles = []
        subtitles.append(sub)
        listitem.setSubtitles(subtitles)

    xbmcplugin.setResolvedUrl(_handle, True, listitem)

def history():
    name_list = open(history_path, "r", encoding="utf-8").read().splitlines()
    for category in name_list:
        list_item = xbmcgui.ListItem(label=category)
        url = get_url(action='listing_search', name=category)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def search(name, params=None):
    if name == "None":
        kb = xbmc.Keyboard("", 'Zadejte název filmu nebo seriálu')
        kb.doModal()
        if not kb.isConfirmed():
            return
        q = kb.getText()
        if q == "":
            return
    else:
        q = encode(name)

    dprint(f'Search(): ' + q)

    ## Save to history
    if os.path.exists(history_path):
        lh = open(history_path, "r").read().splitlines()
        if q not in lh:
            if len(lh) == 10:
                del lh[-1]
            lh.insert(0, unidecode(q))
            f = open(history_path, "w")
            for item in lh:
                f.write("%s\n" % item)
            f.close()
    else:
        f = open(history_path, "w")
        f.write(q)
        f.close()

    videos = _provider.search(q)

    if not videos:
        # Not found. Search Variants.
        new_search = search_variants_dialog(name)
        if new_search is not None:
            search(new_search, params)

        return

    xbmcplugin.setContent(_handle, 'videos')

    dprint('search(): found: ' + str(len(videos)))
    for video in videos[:int(g_max_searched_vids)]:
        #dprint('search(): found item: ' + str(category))
        list_item = xbmcgui.ListItem(label=video[0] + video[1])

        if params is not None and len(params) > 0:
            art = params.get("art", None)
            if art is not None:
                art = json.loads(art)
                list_item.setArt(art)

            video_info = params.get("videoInfo", None)
            if video_info is not None:
                video_info = json.loads(video_info)
                # video_info['title'] = category[0] + category[1]
                video_info['title'] = video[3]
                list_item.setInfo('video', video_info)

        list_item.setProperty('IsPlayable', 'true')
        list_item.addContextMenuItems(
            [
                ('Vybrat stream',
                 'RunPlugin({})'.format(
                     get_url(action="play", link=video[2], force_selector=True))
                 ),
                ('Kopírovat URL', 'RunPlugin({})'.format(get_url(action="copy_url", url=video[2]))),
                ('Uložit do knihovny', 'RunPlugin({})'.format(get_url(action="library", url=video[2]))),
                ('Stáhnout', 'RunPlugin({})'.format(get_url(action="download", url=video[2]))),
                ('QR kód streamu', 'RunPlugin({})'.format(get_url(action="qr", url=video[2])))
            ]
        )
        url = get_url(action='play', link=video[2])
        dprint("search(): add item: " + video[2])

        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # Add button to search variant.
    search_var_item = xbmcgui.ListItem(label='Změnit hledaný výraz')
    search_var_item.setProperty('IsPlayable', 'false')
    sv_url = get_url(action='search_variant', name=name, params=params)
    xbmcplugin.addDirectoryItem(_handle, sv_url, search_var_item, True)

    xbmcplugin.endOfDirectory(_handle)

def search_variant(name: str, params):
    new_search = search_variants_dialog(name)
    if new_search is not None:
        search(new_search, params)

def menu():
    if os.path.exists(history_path):
        name_list = [("Hledat", "listing_search", "None", ""), ("Historie hledání", "listing_history", "None", ""),
                     ("Filmy", "listing_movie_category", "", ""), ("Seriály", "listing_serie_category", "", "")]
    else:
        name_list = [("Hledat", "listing_search", "None", ""), ("Filmy", "listing_movie_category", "", ""),
                     ("Seriály", "listing_serie_category", "", "")]
    for category in name_list:
        list_item = xbmcgui.ListItem(label=category[0])
        url = get_url(action=category[1], name=category[2], type=category[3])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)


def home():
    xbmc.executebuiltin("Dialog.Close(all, true)")  # Zavře všechna okna/dialogy
    xbmc.executebuiltin(f"RunPlugin(plugin://{_ADDON_ID}/)")  # Spustí kořenovou stránku doplňku
    # xbmc.executebuiltin("ActivateWindow(Home)")  # Go to Kodi's main menu
    # xbmc.executebuiltin("Container.Update(plugin://plugin.video.bacprehrajto/, replace)")  # Go to root


def copy_to_clipboard(text: str) -> None:
    dprint(f'copy_to_clipboard(): ' + text)
    ClipboardUtils.copy_to_clipboard(text)


def get_name_ext(download_url: str, content: bytes) -> Tuple[Optional[str], Optional[str]]:
    name_wo_ext: Optional[str] = None
    extension: Optional[str] = None

    filename_groups = find_pattern_groups(download_url, r'filename=(([^&\?]+)\.([^&\?]+))')
    if filename_groups is not None:
        name_wo_ext = filename_groups.group(2)
        extension = filename_groups.group(3)

    if content is not None and (name_wo_ext is None or extension is None):
        content_str = content.decode('utf-8')
        # Non-premium link does looks like:
        if name_wo_ext is None:
            name_wo_ext = find_pattern(content_str, r'N.zev souboru:<\/span>\s*?<span>([^<]+?)<\/span>')

        # .....f5DfDqhRyiVeuZxf9gteE.mp4?token=....
        if extension is None:
            extension = find_pattern(download_url, r'\.([a-zA-Z0-9]+)[&\?]token')
            if extension is None:
                extension = find_pattern(content_str, r'Form.t:</span>\s*?<span>([^<]+?)</span>')

    # name = parsed1.split("/")[1] + "." + parsed2.split(".")[-1]
    if name_wo_ext is None:
        parsed1 = urlparse(download_url).path
        name_wo_ext = parsed1.split("/")[1]

    if name_wo_ext is not None:
        # Ensure allowed name for further use.
        name_wo_ext = unquote(name_wo_ext).strip('. ').replace(' ', '.')

    return name_wo_ext, extension


def download_subtitles(
        subs: Optional[List[SubData]], name_wo_ext: str,
        use_name_as_subfolder: bool = False, path: str = g_download_path
) -> Optional[List[str]]:
    if subs is None or len(subs) == 0:
        return None

    # TODO: Delete cache.
    delete_subtitles(subs, name_wo_ext, use_name_as_subfolder, True, path)

    sub_paths: List[str] = []

    if use_name_as_subfolder:
        path = path + "/" + name_wo_ext + "/"
        dprint('download_subtitles(): ' + path)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    for sub in subs:
        name_prefix = "" if use_name_as_subfolder else (name_wo_ext + "-")
        name_subtitles = name_prefix + sub.label + ".srt"
        us = urlopen(sub.path).read()

        abs_path = path + name_subtitles
        fs = open(abs_path, "wb")
        fs.write(us)
        fs.close()

        file_size = get_file_size_human_readable(abs_path, 0)
        new_path = path + name_prefix + sub.label + ' (' + file_size + ')' + '.srt'
        os.rename(abs_path, new_path)

        sub_paths.append(new_path)

    return sub_paths

def delete_subtitles(
        subs: List[SubData], name_wo_ext: str,
        use_name_as_subfolder: bool = False,
        all_except_name: bool = False,
        path: str = g_download_path
):
    if subs is None or len(subs) == 0:
        return

    if use_name_as_subfolder:
        path = path + "/" + name_wo_ext

    try:
        if all_except_name:
            # TODO.
            os.chdir(path)
            for item in os.listdir(os.getcwd()):
                if item != name_wo_ext:
                    os.remove(item)
        else:
            for sub in subs:
                name_prefix = "" if use_name_as_subfolder else (name_wo_ext + "-")
                #name_size_suffix = (name_wo_ext + "-") if use_name_as_subfolder else ""
                name_subtitles = name_prefix + sub.label + ".srt"
                os.remove(path + name_subtitles)
            os.remove(path)
    except Exception as e:
        dprint('delete_subtitles(): could not delete subtitles:\n' + str(e))
        return


def download(download_url: str) -> None:
    if addon.getSetting("download") == "":
        xbmcgui.Dialog().notification(
            "Přehraj.to",
            "Nastavte složku pro stahování",
            xbmcgui.NOTIFICATION_ERROR,
            4000
        )
        return

    content = requests.get(download_url).content

    streams: Optional[List[StreamData]]
    subs: Optional[List[SubData]]
    streams, subs = _provider.get_streams_data(content)
    if streams is None or len(streams) == 0:
        return

    file, selected_premium = open_stream_selector(streams)

    premium, cookies = get_premium()
    # if premium == 1 or selected_premium:
    if selected_premium:
        ### TODO: FIX downloading
        dprint('download(): premium file: ' + file)
        res = requests.get(file, allow_redirects=False)
        # res = requests.get(file, cookies=cookies, allow_redirects=False)
        if res.headers.keys().__contains__('Location'):
            file = res.headers['Location']

            dprint('download(): location: ' + res.headers['Location'])
            dprint('download(): headers: ' + str(res.headers))

        dprint('download(): premium file2: ' + file)

    name_wo_ext, extension = get_name_ext(file, content)

    name = (name_wo_ext if name_wo_ext is not None else "downloaded") + (
                "." + extension) if extension is not None else ""

    # Save subtitles.
    download_subtitles(subs, name_wo_ext)

    # Prepare video download file.
    download_file_path = g_download_path + name
    u = urlopen(file)
    f = open(download_file_path, "wb")
    file_size = int(u.getheader("Content-Length"))

    dialog = xbmcgui.DialogProgress()
    dialog.create("Přehraj.to", "Stahování...")

    start = time.time()
    file_size_dl = 0
    block_sz = 4096
    canceled = False

    # Prepare data for update dialog:
    # Velikost, komprese.
    du_conv_size = convert_size(file_size)
    is_compressed = not selected_premium
    du_compressed_str = "      (komprimováno)" if is_compressed else ""
    du_truncated_name = truncate_middle(name)

    while True:
        if dialog.iscanceled():
            canceled = True
            break

        buffer = u.read(block_sz)
        if not buffer: break
        file_size_dl += len(buffer)
        f.write(buffer)

        # 1. Progress percentage
        status = r"%3.2f%%" % (file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)  # erase old line

        # 3. Speed + ETA + čas dokončení
        elapsed = time.time() - start
        speed = "0.0" if elapsed <= 0 else f"{(file_size_dl / elapsed) / 100000:.1f}"
        if elapsed > 0 and file_size_dl > 0:
            bytes_per_sec = file_size_dl / elapsed
            remaining_bytes = file_size - file_size_dl
            eta_seconds = remaining_bytes / bytes_per_sec if bytes_per_sec > 0 else None
        else:
            eta_seconds = None

        eta_str, finish_str = format_eta_and_finish(eta_seconds)

        # 4. Aktualizace dialogu
        dialog.update(
            int(file_size_dl * 100 / file_size),
            "Velikost:  " + du_conv_size + du_compressed_str + "\n"
            + "Staženo:  " + status + "     Rychlost: " + speed + " Mb/s\n"
            + "Hotovo za: " + eta_str + "       Hotovo v:  " + finish_str + "\n"
            + du_truncated_name
        )

    f.close()
    dialog.close()

    if not canceled:
        dialog = xbmcgui.Dialog()
        dialog.ok('Přehraj.to', 'Soubor stažen\n' + name)
    else:
        os.remove(download_file_path)
        delete_subtitles(subs, name_wo_ext)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params["action"] == "home":
            home()
        if params["action"] == "listing_search":
            search(params["name"], params)
        if params["action"] == "search_variant":
            search_variant(params["name"], params)
        elif params["action"] == "listing_history":
            history()
        elif params["action"].__contains__("listing_") or params["action"] == "search_tmdb":
            tmdb_router(_handle, _url, params)
        elif params["action"] == "play":
            premium, cookies = get_premium()
            if premium == 1:  ## Not necessary...
                play_video_premium(params["link"], cookies)
            else:
                force_selector = params.__contains__("force_selector") and params["force_selector"] == 'True'
                play_video(params["link"], force_selector)
        elif params["action"] == "library":
            if addon.getSetting("library") == "":
                xbmcgui.Dialog().notification(
                    "Přehraj.to", "Nastavte složku pro knihovnu",
                    xbmcgui.NOTIFICATION_ERROR, 3000
                )
                return
            parsed1 = urlparse(params["url"]).path
            name = parsed1.split("/")[1]
            kb = xbmc.Keyboard(name.replace("-", " "), 'Zadejte název a rok filmu')
            kb.doModal()
            if not kb.isConfirmed():
                return
            q = kb.getText()
            if q == "":
                return
            f = open(addon.getSetting("library") + q + ".strm", "w")
            f.write("plugin://plugin.video.bacprehrajto/?action=play&link=" + params["url"])
            f.close()
            xbmcgui.Dialog().notification("Přehraj.to", "Uloženo", xbmcgui.NOTIFICATION_INFO, 3000, sound=False)
        elif params["action"] == "qr":
            u = requests.get(params["url"]).content
            streams, subs = _provider.get_streams_data(u)
            selected_file = open_stream_selector(streams)
            if selected_file is None:
                # Canceled.
                return

            qr_link = "https://quickchart.io/qr?text=" + selected_file.replace('&', '%26')
            dprint("qr: " + qr_link)
            xbmc.executebuiltin('ShowPicture(' + qr_link + ')')
        elif params["action"] == "copy_url":
            copy_to_clipboard(params["url"])
        elif params["action"] == "download":
            download(params["url"])
    else:
        menu()


if __name__ == '__main__':
    router(sys.argv[2][1:])
