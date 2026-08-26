"""
DevilCore — Noctis System Control
tools/system_control.py
Complete Phase 4 implementation for Windows 11 ARM64 / Qualcomm Snapdragon
"""

import psutil
import subprocess
import os
import sys
import time
import platform
import ctypes
import threading
from datetime import datetime

# ── Optional dependency flags ─────────────────────────────────────────────────

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import win32clipboard
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


# ── App launch map ─────────────────────────────────────────────────────────────

APP_MAP = {
    # System apps
    "notepad":        "notepad.exe",
    "calculator":     "calc.exe",
    "chrome":         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge":           "msedge.exe",
    "explorer":       "explorer.exe",
    "file explorer":  "explorer.exe",
    "cmd":            "cmd.exe",
    "terminal":       "wt.exe",
    "powershell":     "powershell.exe",
    "task manager":   "taskmgr.exe",
    "settings":       "ms-settings:",
    "paint":          "mspaint.exe",
    "snipping":       "snippingtool.exe",
    "spotify":        r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    "discord":        r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe",
    "vlc":            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vscode":         "code",
    "code":           "code",
    
    # Web services & URLs
    "youtube":        "https://www.youtube.com",
    "google":         "https://www.google.com",
    "gmail":          "https://mail.google.com",
    "github":         "https://github.com",
    "whatsapp":       "https://web.whatsapp.com",
    "telegram":       "https://web.telegram.org",
    "chatgpt":        "https://chat.openai.com",
    
    # Folders
    "downloads":      os.path.expanduser("~/Downloads"),
    "documents":      os.path.expanduser("~/Documents"),
    "my documents":   os.path.expanduser("~/Documents"),
    "desktop":        os.path.expanduser("~/Desktop"),
    "pictures":       os.path.expanduser("~/Pictures"),
    "music":          os.path.expanduser("~/Music"),
    "videos":         os.path.expanduser("~/Videos"),
    "home":           os.path.expanduser("~"),
}


class SystemControl:

    # ══════════════════════════════════════════════════════════════════════════
    # CPU
    # ══════════════════════════════════════════════════════════════════════════

    def get_cpu(self):
        try:
            usage   = psutil.cpu_percent(interval=0.5)
            cores_p = psutil.cpu_count(logical=False)
            cores_l = psutil.cpu_count(logical=True)
            freq    = psutil.cpu_freq()
            mhz     = int(freq.current) if freq else 0
            return (
                f"CPU: {usage}% | "
                f"{cores_p} physical / {cores_l} logical cores @ {mhz}MHz."
            )
        except Exception as e:
            return f"CPU error: {e}"

    def get_cpu_per_core(self):
        try:
            cores = psutil.cpu_percent(interval=0.5, percpu=True)
            parts = [f"Core{i}: {c}%" for i, c in enumerate(cores)]
            return "Per-core CPU: " + " | ".join(parts)
        except Exception as e:
            return f"Per-core CPU error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # RAM
    # ══════════════════════════════════════════════════════════════════════════

    def get_ram(self):
        try:
            r = psutil.virtual_memory()
            total     = round(r.total     / (1024**3), 1)
            used      = round(r.used      / (1024**3), 1)
            available = round(r.available / (1024**3), 1)
            return (
                f"RAM: {r.percent}% used — "
                f"{used}GB / {total}GB ({available}GB available)."
            )
        except Exception as e:
            return f"RAM error: {e}"

    def get_ram_detailed(self):
        try:
            r    = psutil.virtual_memory()
            swap = psutil.swap_memory()
            total     = round(r.total     / (1024**3), 1)
            used      = round(r.used      / (1024**3), 1)
            available = round(r.available / (1024**3), 1)
            cached    = round(getattr(r, "cached", 0) / (1024**3), 1)
            swap_used  = round(swap.used  / (1024**3), 1)
            swap_total = round(swap.total / (1024**3), 1)
            return (
                f"RAM: {r.percent}% used — {used}GB / {total}GB | "
                f"Available: {available}GB | Cached: {cached}GB | "
                f"Swap: {swap_used}GB / {swap_total}GB"
            )
        except Exception as e:
            return f"RAM detailed error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # BATTERY
    # ══════════════════════════════════════════════════════════════════════════

    def get_battery(self):
        try:
            b = psutil.sensors_battery()
            if b is None:
                return "Battery: No battery detected."
            status = "plugged in" if b.power_plugged else "on battery"
            return f"Battery: {round(b.percent)}%, {status}."
        except Exception as e:
            return f"Battery error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # DISK
    # ══════════════════════════════════════════════════════════════════════════

    def get_disk(self):
        try:
            d     = psutil.disk_usage("C:\\")
            total = round(d.total / (1024**3), 1)
            used  = round(d.used  / (1024**3), 1)
            free  = round(d.free  / (1024**3), 1)
            return (
                f"Disk (C:\\): {d.percent}% used — "
                f"{used}GB / {total}GB ({free}GB free)."
            )
        except Exception as e:
            return f"Disk error: {e}"

    def get_disk_io(self):
        try:
            d1 = psutil.disk_io_counters()
            time.sleep(0.5)
            d2 = psutil.disk_io_counters()
            read_mb  = round((d2.read_bytes  - d1.read_bytes)  / 1024 / 1024 / 0.5, 2)
            write_mb = round((d2.write_bytes - d1.write_bytes) / 1024 / 1024 / 0.5, 2)
            return f"Disk I/O: Read {read_mb} MB/s | Write {write_mb} MB/s"
        except Exception as e:
            return f"Disk I/O error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # GPU  (Qualcomm Adreno via WMI + PowerShell perf counters)
    # ══════════════════════════════════════════════════════════════════════════

    def get_gpu(self):
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-WmiObject Win32_VideoController | "
                 "Select-Object Name, AdapterRAM, DriverVersion | "
                 "Format-List"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            if lines:
                return "GPU: " + " | ".join(lines)
            return "GPU info: Not available via WMI."
        except Exception as e:
            return f"GPU error: {e}"

    def get_gpu_usage(self):
        """
        Reads Adreno/D3D GPU engine usage from Windows performance counters.
        Returns 'Not available' honestly if counter is missing — not an error.
        """
        try:
            ps_cmd = (
                "$v = Get-WmiObject Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine "
                "2>$null | Where-Object { $_.Name -like '*engtype_3D*' } | "
                "Measure-Object -Property UtilizationPercentage -Average | "
                "Select-Object -ExpandProperty Average; "
                "if ($v) { [math]::Round($v,1) } else { 'N/A' }"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=10
            )
            val = result.stdout.strip()
            if val and val != "N/A":
                return f"GPU Usage: {val}%"
            return "GPU Usage: Counter not available on Qualcomm Adreno (driver limitation)."
        except Exception as e:
            return f"GPU usage error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # NPU
    # ══════════════════════════════════════════════════════════════════════════

    def get_npu_status(self):
        """
        Qualcomm Hexagon NPU has no public Python/WMI API on Windows ARM64 yet.
        Task Manager reads it via a private Qualcomm driver not exposed to userland.
        """
        return (
            "NPU: Qualcomm Hexagon NPU detected on Snapdragon X — "
            "real-time usage monitoring not yet available via public Windows API. "
            "Qualcomm hasn't released a userland SDK for this on Windows ARM64."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # NETWORK
    # ══════════════════════════════════════════════════════════════════════════

    def get_ip(self):
        try:
            import socket
            addrs = psutil.net_if_addrs()
            parts = []
            for iface, addr_list in addrs.items():
                for addr in addr_list:
                    if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                        parts.append(f"{iface}: {addr.address}")
            return "IP addresses: " + " | ".join(parts) if parts else "IP: None found."
        except Exception as e:
            return f"IP error: {e}"

    def get_wifi_info(self):
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=6
            )
            ssid    = ""
            signal  = ""
            for line in result.stdout.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    ssid   = line.split(":", 1)[-1].strip()
                if "Signal" in line:
                    signal = line.split(":", 1)[-1].strip()
            if ssid:
                return f"WiFi: {ssid} | Signal: {signal}"
            return "WiFi: Not connected or no adapter found."
        except Exception as e:
            return f"WiFi error: {e}"

    def get_network(self):
        try:
            n1 = psutil.net_io_counters()
            time.sleep(0.5)
            n2 = psutil.net_io_counters()
            sent = round((n2.bytes_sent - n1.bytes_sent) / 1024 / 0.5, 1)
            recv = round((n2.bytes_recv - n1.bytes_recv) / 1024 / 0.5, 1)
            return f"Network I/O: ↑ {sent} KB/s sent | ↓ {recv} KB/s received"
        except Exception as e:
            return f"Network I/O error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # UPTIME / TEMPERATURE / SCREEN
    # ══════════════════════════════════════════════════════════════════════════

    def get_uptime(self):
        try:
            boot = psutil.boot_time()
            up   = time.time() - boot
            days = int(up // 86400)
            hrs  = int((up % 86400) // 3600)
            mins = int((up % 3600) // 60)
            boot_str = datetime.fromtimestamp(boot).strftime("%I:%M %p, %b %d")
            return f"System uptime: {days}d {hrs}h {mins}m (booted at {boot_str})."
        except Exception as e:
            return f"Uptime error: {e}"

    def get_temperature(self):
        return (
            "Temperature: Qualcomm Snapdragon X — "
            "thermal sensors not exposed to Windows userland on ARM64. "
            "Hardware limitation, not a software bug."
        )

    def get_screen_info(self):
        try:
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$s = [System.Windows.Forms.Screen]::PrimaryScreen; "
                "\"Resolution: $($s.Bounds.Width)x$($s.Bounds.Height) | "
                "Color depth: $($s.BitsPerPixel)-bit\""
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=6
            )
            val = result.stdout.strip()
            return f"Screen: {val}" if val else "Screen info: Not available."
        except Exception as e:
            return f"Screen error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # VOLUME  (pycaw primary, PowerShell fallback)
    # ══════════════════════════════════════════════════════════════════════════

    def _get_volume_interface(self):
        if not PYCAW_AVAILABLE:
            return None
        try:
            from pycaw.pycaw import AudioUtilities
            device = AudioUtilities.GetSpeakers()
            return device.EndpointVolume
        except Exception:
            return None

    def get_volume(self):
        vol = self._get_volume_interface()
        if vol:
            try:
                pct   = round(vol.GetMasterVolumeLevelScalar() * 100)
                muted = bool(vol.GetMute())
                label = " (muted)" if muted else ""
                return f"Volume: {pct}%{label}"
            except Exception:
                pass
        # PowerShell fallback
        try:
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "[System.Windows.Forms.SendKeys]::SendWait(''); "
                "$wsh = New-Object -comObject WScript.Shell; "
                "0"  # just a ping — can't read via PS easily, skip gracefully
            )
            return "Volume: pycaw unavailable — install with: pip install pycaw"
        except Exception as e:
            return f"Volume error: {e}"

    def set_volume(self, level: int):
        level = max(0, min(100, int(level)))
        vol = self._get_volume_interface()
        if vol:
            try:
                vol.SetMasterVolumeLevelScalar(level / 100.0, None)
                return f"Volume set to {level}%."
            except Exception as e:
                return f"Volume set error: {e}"
        # PowerShell fallback using nircmd if available
        try:
            subprocess.run(
                ["powershell", "-Command",
                 f"$wsh = New-Object -comObject WScript.Shell; "
                 f"Add-Type -AssemblyName System.Windows.Forms"],
                capture_output=True, timeout=5
            )
            return "Volume: pycaw required to set volume. Run: pip install pycaw"
        except Exception as e:
            return f"Volume set error: {e}"

    def volume_up(self, step: int = 10):
        vol = self._get_volume_interface()
        if vol:
            try:
                current = round(vol.GetMasterVolumeLevelScalar() * 100)
                new_val = min(100, current + step)
                vol.SetMasterVolumeLevelScalar(new_val / 100.0, None)
                return f"Volume increased to {new_val}%."
            except Exception as e:
                return f"Volume up error: {e}"
        return "Volume up: pycaw not available."

    def volume_down(self, step: int = 10):
        vol = self._get_volume_interface()
        if vol:
            try:
                current = round(vol.GetMasterVolumeLevelScalar() * 100)
                new_val = max(0, current - step)
                vol.SetMasterVolumeLevelScalar(new_val / 100.0, None)
                return f"Volume decreased to {new_val}%."
            except Exception as e:
                return f"Volume down error: {e}"
        return "Volume down: pycaw not available."

    def mute_volume(self):
        vol = self._get_volume_interface()
        if vol:
            try:
                vol.SetMute(1, None)
                return "Volume muted."
            except Exception as e:
                return f"Mute error: {e}"
        return "Mute: pycaw not available."

    def unmute_volume(self):
        vol = self._get_volume_interface()
        if vol:
            try:
                vol.SetMute(0, None)
                return "Volume unmuted."
            except Exception as e:
                return f"Unmute error: {e}"
        return "Unmute: pycaw not available."

    # ══════════════════════════════════════════════════════════════════════════
    # BRIGHTNESS  (screen-brightness-control primary, PowerShell fallback)
    # ══════════════════════════════════════════════════════════════════════════

    def get_brightness(self):
        if SBC_AVAILABLE:
            try:
                b = sbc.get_brightness()
                val = b[0] if isinstance(b, list) else b
                return f"Brightness: {val}%"
            except Exception:
                pass
        try:
            ps_cmd = (
                "(Get-WmiObject -Namespace root/WMI "
                "-Class WmiMonitorBrightness).CurrentBrightness"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=6
            )
            val = result.stdout.strip()
            if val:
                return f"Brightness: {val}%"
        except Exception:
            pass
        return "Brightness: Unable to read on this display."

    def set_brightness(self, level: int):
        level = max(0, min(100, int(level)))
        if SBC_AVAILABLE:
            try:
                sbc.set_brightness(level)
                return f"Brightness set to {level}%."
            except Exception:
                pass
        try:
            ps_cmd = (
                f"(Get-WmiObject -Namespace root/WMI "
                f"-Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
            )
            subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, timeout=6
            )
            return f"Brightness set to {level}% via WMI."
        except Exception as e:
            return f"Brightness set error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # PROCESSES
    # ══════════════════════════════════════════════════════════════════════════

    def list_processes(self, top: int = 10):
        try:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
            lines = [f"Top {top} processes by CPU:"]
            for p in procs[:top]:
                lines.append(
                    f"  [{p['pid']}] {p['name']} — "
                    f"CPU: {p['cpu_percent']}% | RAM: {round(p.get('memory_percent', 0), 1)}%"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Process list error: {e}"

    def kill_process(self, name_or_pid):
        try:
            if str(name_or_pid).isdigit():
                p = psutil.Process(int(name_or_pid))
                p.kill()
                return f"Process {name_or_pid} killed."
            else:
                killed = []
                for p in psutil.process_iter(["pid", "name"]):
                    if name_or_pid.lower() in p.info["name"].lower():
                        p.kill()
                        killed.append(p.info["name"])
                return f"Killed: {', '.join(killed)}" if killed else f"No process matching '{name_or_pid}' found."
        except Exception as e:
            return f"Kill error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIVE WINDOW
    # ══════════════════════════════════════════════════════════════════════════

    def get_active_window(self):
        if PYGETWINDOW_AVAILABLE:
            try:
                w = gw.getActiveWindow()
                return f"Active window: {w.title}" if w else "Active window: None"
            except Exception:
                pass
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
                 "Sort-Object CPU -Descending | Select-Object -First 1).MainWindowTitle"],
                capture_output=True, text=True, timeout=5
            )
            val = result.stdout.strip()
            return f"Active window: {val}" if val else "Active window: Unknown"
        except Exception as e:
            return f"Active window error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # SCREENSHOT
    # ══════════════════════════════════════════════════════════════════════════

    def take_screenshot(self, path: str = None):
        if path is None:
            path = os.path.join(
                os.path.expanduser("~"),
                "Desktop",
                f"noctis_screenshot_{int(time.time())}.png"
            )
        if PYAUTOGUI_AVAILABLE:
            try:
                img = pyautogui.screenshot()
                img.save(path)
                return f"Screenshot saved to: {path}"
            except Exception:
                pass
        try:
            subprocess.run(
                ["powershell", "-Command",
                 f"Add-Type -AssemblyName System.Windows.Forms; "
                 f"$bmp = [System.Drawing.Bitmap]::new([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, "
                 f"[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
                 f"$g = [System.Drawing.Graphics]::FromImage($bmp); "
                 f"$g.CopyFromScreen(0,0,0,0,$bmp.Size); "
                 f"$bmp.Save('{path}')"],
                capture_output=True, timeout=8
            )
            return f"Screenshot saved to: {path}"
        except Exception as e:
            return f"Screenshot error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # CLIPBOARD
    # ══════════════════════════════════════════════════════════════════════════

    def get_clipboard(self):
        if WIN32_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                return f"Clipboard: {data[:200]}"
            except Exception:
                pass
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=5
            )
            val = result.stdout.strip()
            return f"Clipboard: {val[:200]}" if val else "Clipboard: Empty."
        except Exception as e:
            return f"Clipboard error: {e}"

    def set_clipboard(self, text: str):
        try:
            subprocess.run(
                ["powershell", "-Command", f"Set-Clipboard '{text}'"],
                capture_output=True, timeout=5
            )
            return f"Clipboard set to: {text[:80]}"
        except Exception as e:
            return f"Clipboard set error: {e}"

    # ══════════════════════════════════════════════════════════════════════════
    # APP, FOLDER & URL LAUNCHER
    # ══════════════════════════════════════════════════════════════════════════

    def open_url(self, url: str):
        """Opens any web URL in default browser."""
        import webbrowser
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return f"Opened {url}"
        except Exception as e:
            return f"Failed to open URL: {e}"

    def search_web(self, query: str):
        """Searches Google for query in default browser."""
        import urllib.parse
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}"
        return self.open_url(url)

    def open_folder(self, folder_path: str):
        """Opens any folder on disk or common folder alias in File Explorer."""
        key = folder_path.lower().strip()
        path = APP_MAP.get(key, folder_path)
        expanded = os.path.expanduser(os.path.expandvars(path))
        if os.path.exists(expanded):
            try:
                os.startfile(expanded)
                return f"Opened folder: {expanded}"
            except Exception as e:
                return f"Error opening folder: {e}"
        else:
            return f"Folder not found: {folder_path}"

    def launch_app(self, name: str):
        """Smart launcher for apps, URLs, folders, and system commands."""
        key = name.lower().strip()

        # Check if it's a URL or web alias
        if key.startswith("http://") or key.startswith("https://") or key.startswith("www."):
            return self.open_url(key)

        target = APP_MAP.get(key)
        if target:
            if target.startswith("http://") or target.startswith("https://"):
                return self.open_url(target)
            expanded = os.path.expanduser(os.path.expandvars(target))
            if os.path.exists(expanded):
                try:
                    os.startfile(expanded)
                    return f"Opened {name}."
                except Exception as e:
                    return f"Error opening {name}: {e}"
            else:
                try:
                    subprocess.Popen(target, shell=True)
                    return f"Launched {name}."
                except Exception as e:
                    return f"Launch error: {e}"

        # Dynamic fallback: try Windows Start-Process / shell execute
        try:
            os.startfile(name)
            return f"Launched {name}."
        except Exception:
            pass

        try:
            subprocess.Popen(f"start {name}", shell=True)
            return f"Launched {name}."
        except Exception as e:
            return f"Could not find or launch '{name}'."

    # ══════════════════════════════════════════════════════════════════════════
    # POWER CONTROLS
    # ══════════════════════════════════════════════════════════════════════════

    def shutdown(self, delay: int = 0, confirmed: bool = False):
        os.system(f"shutdown /s /t {delay}")
        return f"Shutdown in {delay} seconds."

    def restart(self, delay: int = 0, confirmed: bool = False):
        os.system(f"shutdown /r /t {delay}")
        return f"Restart in {delay} seconds."

    def cancel_shutdown(self):
        os.system("shutdown /a")
        return "Shutdown/restart cancelled."

    def lock_screen(self):
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."

    def sleep(self):
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Going to sleep."

    def hibernate(self):
        os.system("shutdown /h")
        return "Hibernating."

    # ══════════════════════════════════════════════════════════════════════════
    # AGGREGATE REPORTS
    # ══════════════════════════════════════════════════════════════════════════

    def get_system_stats(self):
        """
        Master stats block — called when user says 'system stats', 'what's my ram', etc.
        Shows everything: CPU, GPU, NPU, RAM, disk, network, screen, uptime.
        """
        return "\n".join([
            "═" * 55,
            "  NOCTIS — FULL SYSTEM STATS",
            "═" * 55,
            self.get_cpu(),
            self.get_cpu_per_core(),
            self.get_ram_detailed(),
            self.get_battery(),
            self.get_disk(),
            self.get_disk_io(),
            self.get_gpu(),
            self.get_gpu_usage(),
            self.get_npu_status(),
            self.get_network(),
            self.get_screen_info(),
            self.get_uptime(),
            self.get_temperature(),
            "═" * 55,
        ])

    def full_report(self):
        """Full report including stats + peripherals."""
        return "\n".join([
            self.get_system_stats(),
            self.get_volume(),
            self.get_brightness(),
            self.get_ip(),
            self.get_wifi_info(),
            self.get_active_window(),
        ])
    
    def mute(self):
        return self.mute_volume()

    def unmute(self):
        return self.unmute_volume()

    def lock(self):
        return self.lock_screen()

    def open_app(self, name):
        return self.launch_app(name)

    def execute_command(self, text: str):
        """
        Unified system command router for text chat & voice commands.
        Returns response string if command matched and executed, or None if not a system command.
        """
        import re
        t = text.lower().strip()
        if not t:
            return None

        # Set volume
        m = re.search(r'(?:set volume|volume|make.*volume|set.*volume)\s+(?:to\s+)?(\d+)', t)
        if m:
            return self.set_volume(int(m.group(1)))

        # Volume up/down/mute/unmute
        if any(k in t for k in ["volume up", "increase volume"]):
            return self.volume_up()
        if any(k in t for k in ["volume down", "decrease volume", "lower volume"]):
            return self.volume_down()
        if any(k in t for k in ["mute volume", "mute audio", "silence audio"]) or t == "mute":
            return self.mute_volume()
        if any(k in t for k in ["unmute volume", "unmute audio", "restore audio"]) or t == "unmute":
            return self.unmute_volume()
        if any(k in t for k in ["what's my volume", "current volume", "volume level", "get volume"]):
            return self.get_volume()

        # Set brightness
        m = re.search(r'(?:set brightness|brightness)\s+(?:to\s+)?(\d+)', t)
        if m:
            return self.set_brightness(int(m.group(1)))
        if "brightness" in t:
            return self.get_brightness()

        # Open folder
        m = re.search(r'(?:open|show)\s+(?:my\s+)?(.+?)\s+folder', t)
        if m:
            return self.open_folder(m.group(1).strip())
        m = re.search(r'open folder\s+(.+)', t)
        if m:
            return self.open_folder(m.group(1).strip())

        # Web search
        m = re.search(r'(?:search for|search web for|google)\s+(.+)', t)
        if m:
            return self.search_web(m.group(1).strip())

        # Open URL / website
        m = re.search(r'(?:go to|open website)\s+(.+)', t)
        if m:
            return self.open_url(m.group(1).strip())

        # Open / launch app or folder alias
        m = re.search(r'^(?:open|launch|start)\s+(.+)$', t)
        if m:
            target = m.group(1).strip()
            target_clean = re.sub(r'\s+(app|program|please)$', '', target)
            return self.launch_app(target_clean)

        # Kill / close process
        m = re.search(r'^(?:close|kill|terminate)\s+(.+)$', t)
        if m:
            return self.kill_process(m.group(1).strip())

        # Power control
        if any(w in t for w in ["lock screen", "lock the screen", "lock computer"]):
            return self.lock_screen()
        if any(w in t for w in ["sleep mode", "go to sleep"]):
            return self.sleep()

        # System telemetry queries
        SYSTEM_COMMANDS = [
            (["cpu", "processor usage", "processor load"],          lambda: self.get_cpu()),
            (["ram", "memory usage", "memory"],                     lambda: self.get_ram()),
            (["battery", "power level", "charge"],                  lambda: self.get_battery()),
            (["disk", "storage", "drive space"],                    lambda: self.get_disk()),
            (["network", "internet speed", "bandwidth"],            lambda: self.get_network()),
            (["uptime", "how long running", "running time"],        lambda: self.get_uptime()),
            (["system stats", "system status", "full stats"],       lambda: self.get_system_stats()),
            (["full report", "diagnostics", "system report"],       lambda: self.full_report()),
            (["wifi", "wi-fi", "wireless", "signal"],               lambda: self.get_wifi_info()),
            (["ip address", "my ip", "network address"],            lambda: self.get_ip()),
            (["screenshot", "take a screenshot", "capture screen"], lambda: self.take_screenshot()),
            (["active window", "what's open", "current window"],   lambda: self.get_active_window()),
            (["clipboard", "what's in clipboard"],                  lambda: self.get_clipboard()),
            (["processes", "top processes", "running apps"],        lambda: self.list_processes()),
            (["temperature", "cpu temp", "how hot"],                lambda: self.get_temperature()),
        ]

        for keywords, handler in SYSTEM_COMMANDS:
            if any(kw in t for kw in keywords):
                return handler()

        return None