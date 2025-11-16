import os
import re
from typing import Optional

import requests


# Expecting 01:54:22 or 00:54:41
def crop_time(time_str: str) -> str:
    if len(time_str) != 8:
        return time_str

    split_time = time_str.split(':')
    if split_time[0] != "00":
        return time_str

    return split_time[1] + ':' + split_time[2]


def truncate_middle(s, n=50):
    # Check if string is already short enough
    if len(s) <= n:
        return s

    # Look for SxxExx pattern (e.g., S01E05)
    match = re.search(r'S\d{2}E\d{2}', s)
    if match:
        # Get the SxxExx part
        season_episode = match.group(0)
        # Get index of the match
        start_idx = match.start()
        end_idx = match.end()

        # Keep first 3 characters before SxxExx
        before = s[:start_idx][:3]
        # Keep everything after SxxExx
        after = s[end_idx:]

        # Combine the parts with "..." between them
        result = before + "..." + season_episode + "..." + after

        # If the result is still too long, truncate
        if len(result) <= n:
            return result
        # Truncate middle of the result
        n_2 = int(n / 2 - 3)
        n_1 = n - n_2 - 3
        return '{0}...{1}'.format(result[:n_1], result[-n_2:])

    # If no SxxExx pattern, use original truncation
    n_2 = int(n / 2 - 3)
    n_1 = n - n_2 - 3
    return '{0}...{1}'.format(s[:n_1], s[-n_2:])


def contains_pattern(source, pattern):
    pattern = re.compile(pattern, re.DOTALL)
    return pattern.search(source) is not None


def find_pattern(source: str, pattern: str) -> Optional[str]:
    pattern = re.compile(pattern, re.DOTALL)
    result = pattern.search(source)
    if result is None:
        return None

    return result.group(1)

def find_pattern_groups(source, pattern):
    pattern = re.compile(pattern, re.DOTALL)
    result = pattern.search(source)
    if result is None:
        return None

    return result


def get_file_size_human_readable(file_path: str, precision: int = 1, xbmc=None) -> Optional[str]:
    """
    Returns file size as a formatted string (e.g., "1.23 GB" or "456 MB").
    Returns None if size cannot be determined.
    """
    try:
        if file_path.startswith(('http://', 'https://')):
            # Remote file: Check Content-Length header
            response = requests.head(file_path, allow_redirects=True, timeout=5)
            size_bytes = int(response.headers.get('Content-Length', 0))
        else:
            # Local file
            size_bytes = os.path.getsize(file_path)

        # Convert to human-readable format
        return convert_size(size_bytes, precision)
    except (requests.RequestException, OSError) as e:
        if xbmc:
            xbmc.log(f"Failed to get file size for: {file_path}\n{e}", xbmc.LOGWARNING)
        return None


def convert_size(number_of_bytes: int, precision: int = 1):
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")
    step_to_greater_unit = 1024.
    number_of_bytes = float(number_of_bytes)
    unit = 'B'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'
    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'
    number_of_bytes = round(number_of_bytes, precision)
    return format(number_of_bytes, '.'+str(precision)+'f') + ' ' + unit
