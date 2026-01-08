import subprocess


def get_active_window_context():
    """Return the active window context (application name) using X11."""
    try:
        # Get the active window ID
        root_out = subprocess.check_output(
            ['xprop', '-root', '_NET_ACTIVE_WINDOW'], text=True)
        window_id = root_out.split()[-1]

        # Get the WM_CLASS which usually contains the app name
        window_out = subprocess.check_output(
            ['xprop', '-id', window_id, 'WM_CLASS'], text=True)
        # Standard format: WM_CLASS(STRING) = "instance", "class"
        context = window_out.split('=')[-1].strip().replace('"', '').split(',')[-1].strip()
        return context
    except Exception:
        return "Unknown-Context"
