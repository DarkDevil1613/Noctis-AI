"""
Noctis UI Launcher — opens the Command UI in a native desktop window.
Uses pywebview with EdgeChromium (WebView2) backend — no .NET Framework needed.
"""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYWEBVIEW_GUI'] = 'edgechromium'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import webview
import subprocess
import threading


def on_closed():
    """Called when the UI window is closed. Kills all backend processes."""
    stop_bat = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stop_noctis.bat")
    if os.path.exists(stop_bat):
        subprocess.Popen(
            ["cmd", "/c", stop_bat],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    os._exit(0)


def main():
    ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
    index_path = os.path.join(ui_dir, "index.html")

    if not os.path.exists(index_path):
        print(f"[Noctis UI] ERROR: {index_path} not found.")
        sys.exit(1)

    # Convert to file:// URL for WebView2
    file_url = "file:///" + index_path.replace("\\", "/")

    window = webview.create_window(
        title="Noctis",
        url=file_url,
        width=1200,
        height=750,
        frameless=True,
        easy_drag=False,
        background_color="#0a0a0f",
        text_select=True,
    )

    window.events.closed += on_closed

    webview.start(debug=False, gui='edgechromium')


if __name__ == "__main__":
    main()
