from typing import Optional

import xbmcgui

from modules.generate_prefixes import generate_prefixes


def search_variants_dialog(input_str, heading="Hledej varianty:") -> Optional[str]:
    """
    Shows a Kodi select dialog using prefixes generated from input_str.

    Args:
        input_str (str): Input string to generate options from.
        heading (str): Dialog title.

    Returns:
        str: Selected prefix string, or empty string if cancelled.
    """
    prefixes = generate_prefixes(input_str)
    if not prefixes:
        return None

    dialog = xbmcgui.Dialog()
    selected_idx = dialog.select(heading, prefixes)

    if selected_idx >= 0:
        return prefixes[selected_idx]
    else:
        return None

