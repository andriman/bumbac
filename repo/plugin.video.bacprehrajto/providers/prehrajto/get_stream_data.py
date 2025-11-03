import json
import os
import re
from typing import Tuple, List, Optional

import xbmcgui
from bs4 import BeautifulSoup

import hjson
from common import subtitles_path
from model.StreamData import StreamData
from model.SubData import SubData
from utils.utils import dprint, contains_pattern, find_pattern, filter_subtitles, format_time_ago


def get_streams_data(gl) -> Tuple[Optional[List[StreamData]], Optional[List[SubData]]]:
    dprint(f'get_stream_data()')

    p_dialog: xbmcgui.DialogProgress = xbmcgui.DialogProgress()
    p_dialog.create("Hledám streamy")

    soup = BeautifulSoup(gl, 'html.parser')
    sources_pattern = re.compile('var sources = (\[.*?);', re.DOTALL)

    script_f = soup.find("script", string=sources_pattern)

    if script_f is None:
        dgl = gl.decode('utf-8')
        if contains_pattern(dgl, r'>\s*?Video se zpracov'):
            upload_date = find_pattern(dgl, 'Datum nahr.n.:</span>\s*?<span>([^<]+)')

            # Výpočet kolik hodin zpět
            time_ago = format_time_ago(upload_date)

            p_dialog.close()
            xbmcgui.Dialog().notification(
                heading="Přehraj.to",
                message=f"Video se teprve zpracovává:\nNahráno:\n" + time_ago,
                icon=xbmcgui.NOTIFICATION_INFO,
                time=4000,
                sound=False
            )
        else:
            dprint(f'get_stream_data(): script not found:\n' + str(gl))

            p_dialog.close()
            xbmcgui.Dialog().notification(
                heading="Přehraj.to",
                message=f"Script not found",
                icon=xbmcgui.NOTIFICATION_INFO,
                time=4000,
                sound=False
            )

        return None, None

    script = script_f.string

    stream_items: List[StreamData] = []

    # Videos.
    p_dialog.update(10, "Hledám video streamy")
    try:
        dprint(f'get_stream_data(): vidfile')
        streams = re.compile('file:\s*?["\'](.+?)["\'],\s*?label: ["\'](.+?)["\']', re.DOTALL)
        sources = sources_pattern.findall(script)

        for item in sources:
            all_streams = streams.findall(item)
            dprint(f'get_stream_data(): vidfiles:\n' + str(all_streams))
            for stream in all_streams:
                label = stream[1]
                quality = int(label.strip('p'))
                item = StreamData(label=label, quality=quality, path=stream[0])
                stream_items.append(item)

    except Exception as e:
        dprint(f'get_stream_data(): vidfile exception:\n' + str(e))
        src = re.compile('src:\\s*?["\'](.+?)["\'][^\}]+?label:\s*?["\'](.+?)["\']', re.DOTALL)
        all_streams = src.findall(sources_pattern.findall(script)[0])
        for stream in all_streams:
            label = stream[1]
            quality = int(label.strip('p'))
            item = StreamData(label=label, quality=quality, path=stream[0])
            stream_items.append(item)

    stream_items.sort(key=lambda x: x.quality, reverse=True)

    # Subtitle files.
    p_dialog.update(60, "Hledám titulky")
    try:
        tracks_pattern = re.compile('var tracks = (\[.*?);', re.DOTALL)
        script = soup.find("script", string=tracks_pattern).string
        dprint(f'get_stream_data(): script: ' + str(script))

        sub_data = hjson.loads(tracks_pattern.findall(script)[0])
        sub_data = json.loads(json.dumps(sub_data))

        filtered_sub_data = filter_subtitles(sub_data)
        dprint(f'get_stream_data(): filtered_sub_data: ' + str(filtered_sub_data))
    except Exception as e:
        dprint(f'get_stream_data(): subdata exception:\n' + str(e))
        filtered_sub_data = []

    # Save subtitles.
    # Ensure the directory exists
    os.makedirs(os.path.dirname(subtitles_path), exist_ok=True)

    # sfile_path = subtitles_path + "subtitles.txt"
    # with open(sfile_path, "w+", encoding="utf-8") as f:
    #    f.write(json.dumps(filtered_sub_data))
    #    f.close()

    for sdata in filtered_sub_data:
        sfile_path = subtitles_path + sdata.label + '.txt'
        dprint(f'Sub: ' + sfile_path)
        with open(sfile_path, "w+", encoding="utf-8") as f:
            f.write(sdata.path)
            f.close()

    dprint(f'get_stream_data(): subtitles_path: ' + subtitles_path)

    p_dialog.update(100)
    p_dialog.close()
    return stream_items, filtered_sub_data
