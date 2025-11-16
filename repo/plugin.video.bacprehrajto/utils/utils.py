import re
from typing import List
from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from common import g_is_debug_logs_enabled, quality_icons_path
from model.SubData import SubData
from utils.StrUtils import get_file_size_human_readable


def dprint(text):
    if g_is_debug_logs_enabled:
        print(text)


def filter_subtitles(data) -> List[SubData]:
    dprint(f'filter_subtitles(): data: ' + str(len(data)))

    # Now filter and clean the tracks.
    subtitle_pattern = re.compile(r'- (cze|eng)\d*$', re.IGNORECASE)
    subtitle_pattern2 = re.compile(r'(CZ|EN) -', re.IGNORECASE)

    filtered_tracks: List[SubData] = []
    for track in data:  # assuming dt is the list of track dicts
        label = track.get('label', '')
        match = subtitle_pattern.search(label)
        if not match:
            match = subtitle_pattern2.search(label)

        if match:
            lang_code = match.group(1)
            # If there's a number after cze/eng, include it (e.g., cze1)
            full_match = re.search(r'(cze|eng)\d*$', label, re.IGNORECASE)

            if full_match:
                lang_code = full_match.group(0)  # e.g., "cze", "cze1", "eng"
            else:
                lcu = lang_code.upper()
                if 'CZ' == lcu: lang_code = 'cze'
                elif 'EN' == lcu: lang_code = 'eng'

            file = track.get('file', '')
            if len(file) > 0:
                sub_data = SubData(label=lang_code, path=file)

                if any(x.label == lang_code for x in filtered_tracks):
                    # Prevent skipping/overwriting the subtitle file.
                    sub_data.label = lang_code + '_' + str(len(filtered_tracks))

                filtered_tracks.append(sub_data)

    # Print result
    dprint(f'filter_subtitles(): finish: ' + str(len(data)) + ' -> ' + str(len(filtered_tracks)))
    for t in filtered_tracks:
        dprint(t)

    return filtered_tracks


def notify_file_size(file):
    # Get formatted file size
    file_size_str = "Unknown"
    if file is not None:
        file_size_str = get_file_size_human_readable(file)

    dprint(f'notify_file_size(): ' + file_size_str)

    if file_size_str:
        xbmcgui.Dialog().notification(
            heading="Přehraj.to",
            message=f"Velikost: {file_size_str}",
            icon=xbmcgui.NOTIFICATION_INFO,
            time=4000,
            sound=False
        )


def get_url(url, **kwargs):
    return '{0}?{1}'.format(url, urlencode(kwargs))


def get_quality_icon(q: int):
    icon = 'sd.png'
    if q >= 2160:
        icon = '4k.png'
    elif q >= 1080:
        icon = '1080p.png'
    elif q >= 720:
        icon = '720p.png'

    return quality_icons_path + icon
