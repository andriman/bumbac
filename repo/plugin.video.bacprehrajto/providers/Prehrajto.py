from typing import Tuple, Optional, List
from urllib.parse import quote

import requests
import xbmc
import xbmcgui
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

from common import g_max_searched_vids, addon, g_truncate_titles, g_max_duplicities
from model.StreamData import StreamData
from model.SubData import SubData
from providers._Provider import Provider
from providers.prehrajto.get_stream_data import get_streams_data
from utils.StrUtils import crop_time, truncate_middle
from utils.utils import dprint


class Prehrajto(Provider):

    def search(self, query) -> List[str]:
        max_pages_to_browse = 5
        page = 1
        videos = []
        duplicities_set = []
        duplicities = {}
        dup_counter = 0
        premium = 0

        p_dialog_step = int(100 / g_max_searched_vids)
        p_dialog = xbmcgui.DialogProgress()
        p_dialog.create("Přehraj.to", "Hledám video soubory...")
        p_dialog.update(
            int(len(videos) * p_dialog_step),
            "Strana:         " + str(page) + "\n"
            "Video souborů:  " + str(len(videos)) + "\n"
        )

        if addon.getSetting("email") and len(addon.getSetting("email")) > 0:
            premium, cookies = self.get_premium()

        stop_searching = False
        while not (stop_searching or p_dialog.iscanceled()):
            dprint('search(): processing page: ' + str(page))

            if page > 1:
                xbmc.Monitor().waitForAbort(3)

            if premium == 1:
                html = requests.get('https://prehraj.to:443/hledej/' + quote(query) + '?vp-page=' + str(page),
                                    cookies=cookies).content
            else:
                html = requests.get('https://prehraj.to:443/hledej/' + quote(query) + '?vp-page=' + str(page)).content

            p_dialog.update(
                int(len(videos) * p_dialog_step),
                "Strana:                " + str(page) + "\n"
                "Video souborů:         " + str(len(videos)) + "\n"
                "Duplicit:              " + str(len(duplicities_set)) + "\n"
                "Duplicitních souborů:  " + str(dup_counter) + "\n"
            )

            soup = BeautifulSoup(html, "html.parser")
            title = soup.find_all('h3', attrs={'class': 'video__title'})
            size = soup.find_all('div', attrs={'class': 'video__tag--size'})
            time = soup.find_all('div', attrs={'class': 'video__tag--time'})
            link = soup.find_all('a', {'class': 'video--link'})
            next_button = soup.find_all('a', {'title': 'Zobrazit další'})

            dprint('search(): titles: ' + str(title))

            for t, s, l, m in zip(title, size, link, time):

                if t is None:
                    dprint('search(): Fuckup..')
                    continue

                t = t.text.strip()
                s = s.text.strip()
                m = crop_time(m.text.strip())

                pot_dupl_name = (t + " (" + s + " - " + m + ")")

                duplicitiesVal = duplicities[pot_dupl_name] if duplicities.keys().__contains__(pot_dupl_name) else 0
                if duplicitiesVal is None or duplicitiesVal < g_max_duplicities:
                # if not duplicities_set.__contains__(pot_dupl_name):
                    final_title = t
                    if g_truncate_titles:
                        final_title = truncate_middle(final_title)

                    dprint('search(): final title: ' + final_title)
                    videos.append(
                        (
                            final_title,
                            ' (' + s + " - " + m + ')',
                            'https://prehraj.to:443' + l['href'],
                            t
                        )
                    )
                    dprint('search(): link: ' + l['href'])

                    duplicities[pot_dupl_name] = duplicitiesVal + 1
                else:
                    dup_counter = dup_counter + 1
                    dprint('search(): duplicity: ' + pot_dupl_name + ' x ' + str(dup_counter))
                    duplicities_set.append(pot_dupl_name)

            page = page + 1

            stop_searching = next_button == [] or len(videos) >= int(g_max_searched_vids) or page == max_pages_to_browse

        p_dialog.close()

        return videos

    def get_streams_data(self, src_bytes: bytes) -> Tuple[Optional[List[StreamData]], Optional[List[SubData]]]:
        return get_streams_data(src_bytes)

    def get_premium(self) -> Tuple[bool, RequestsCookieJar]:
        if addon.getSetting("email") != '':
            login = {"password": addon.getSetting("password"),
                     "email": addon.getSetting("email"),
                     '_submit': 'Přihlásit+se',
                     'remember': 'on',
                     '_do': 'login-loginForm-submit'
                     }

            res = requests.post("https://prehraj.to/", login)
            soup = BeautifulSoup(res.content, "html.parser")
            title = soup.find('ul', {'class': 'header__links'})
            title = title.find('span', {'class': 'color-green'})
            if title is None:
                premium = False
                cookies = res.cookies
                xbmcgui.Dialog().notification("Přehraj.to", "Premium účet neaktivní", xbmcgui.NOTIFICATION_INFO, 4000,
                                              sound=False)
            else:
                premium = True
                cookies = res.cookies
                xbmcgui.Dialog().notification("Přehraj.to", "Premium: " + title.text, xbmcgui.NOTIFICATION_INFO, 4000,
                                              sound=False)
        else:
            premium = False
            cookies = None

        return premium, cookies