import xbmc
import xbmcgui
import json
import subprocess
import platform


class ClipboardUtils:
    @staticmethod
    def copy_to_clipboard(text):
        """
        Comprehensive method to copy text to clipboard
        Tries multiple methods in order of reliability
        """
        # Method 1: JSON-RPC (most reliable for Kodi)
        if ClipboardUtils._copy_json_rpc(text):
            return True

        # Method 2: Platform-specific
        if ClipboardUtils._copy_platform(text):
            return True

        # Method 3: Built-in command (least reliable)
        return ClipboardUtils._copy_builtin(text)

    @staticmethod
    def _copy_json_rpc(text):
        """Copy using JSON-RPC"""
        try:
            command = {
                "jsonrpc": "2.0",
                "method": "Application.SetClipboard",
                "params": {"clipboard": text},
                "id": 1
            }
            result = xbmc.executeJSONRPC(json.dumps(command))
            return json.loads(result).get('result', '') == 'OK'
        except Exception as e:
            xbmc.log(f"JSON-RPC clipboard error: {str(e)}", xbmg.LOGERROR)
            return False

    @staticmethod
    def _copy_platform(text):
        """Copy using platform-specific tools"""
        try:
            system = platform.system().lower()

            if system == 'windows':
                subprocess.run(['clip'], input=text.encode('utf-8'), check=True, shell=True)
                return True
            elif system == 'darwin':
                subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
                return True
            elif system == 'linux':
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'],
                                   input=text.encode('utf-8'), check=True)
                    return True
                except:
                    subprocess.run(['xsel', '--clipboard', '--input'],
                                   input=text.encode('utf-8'), check=True)
                    return True
        except Exception as e:
            xbmc.log(f"Platform clipboard error: {str(e)}", xbmc.LOGERROR)
        return False

    @staticmethod
    def _copy_builtin(text):
        """Copy using built-in command"""
        try:
            xbmc.executebuiltin(f"SetClipboard({text})")
            return True
        except Exception as e:
            xbmc.log(f"Built-in clipboard error: {str(e)}", xbmc.LOGERROR)
            return False


# Usage example
def main():
    text_to_copy = "Text to copy to clipboard"

    if ClipboardUtils.copy_to_clipboard(text_to_copy):
        xbmcgui.Dialog().notification(
            "Clipboard",
            "Text copied successfully",
            xbmcgui.NOTIFICATION_INFO,
            3000
        )
    else:
        xbmcgui.Dialog().notification(
            "Error",
            "Failed to copy text",
            xbmcgui.NOTIFICATION_ERROR,
            3000
        )


if __name__ == "__main__":
    main()