import sys
import os
from colorama import init, Fore, Style
import re
from tools.system_control import SystemControl
from dotenv import load_dotenv
load_dotenv()

init(autoreset=True)

sc = SystemControl()

SYSTEM_COMMANDS = [
    (["cpu", "processor usage", "processor load"],          lambda _: sc.get_cpu()),
    (["ram", "memory usage", "memory"],                     lambda _: sc.get_ram()),
    (["battery", "power level", "charge"],                  lambda _: sc.get_battery()),
    (["disk", "storage", "drive space"],                    lambda _: sc.get_disk()),
    (["network", "internet speed", "bandwidth"],            lambda _: sc.get_network()),
    (["uptime", "how long running", "running time"],        lambda _: sc.get_uptime()),
    (["system stats", "system status", "full stats"],       lambda _: sc.get_system_stats()),
    (["full report", "diagnostics", "system report"],       lambda _: sc.full_report()),
    (["wifi", "wi-fi", "wireless", "signal"],               lambda _: sc.get_wifi_info()),
    (["ip address", "my ip", "network address"],            lambda _: sc.get_ip()),
    (["volume up"],                                         lambda _: sc.volume_up()),
    (["volume down"],                                       lambda _: sc.volume_down()),
    (["mute", "silence audio"],                             lambda _: sc.mute()),
    (["unmute", "restore audio"],                           lambda _: sc.unmute()),
    (["lock", "lock screen", "lock the screen"],            lambda _: sc.lock()),
    (["sleep mode", "go to sleep", "suspend"],              lambda _: sc.sleep()),
    (["screenshot", "take a screenshot", "capture screen"], lambda _: sc.take_screenshot()),
    (["active window", "what's open", "current window"],    lambda _: sc.get_active_window()),
    (["clipboard", "what's in clipboard"],                  lambda _: sc.get_clipboard()),
    (["processes", "top processes", "running apps"],        lambda _: sc.list_processes()),
    (["temperature", "cpu temp", "how hot"],                lambda _: sc.get_temperature()),
    (["brightness"],                                        lambda _: sc.get_brightness()),
]

def match_system_command(text):
    t = text.lower().strip()

    m = re.search(r'(?:set volume|volume)\s+(?:to\s+)?(\d+)', t)
    if m:
        return sc.set_volume(int(m.group(1)))

    m = re.search(r'(?:set brightness|brightness)\s+(?:to\s+)?(\d+)', t)
    if m:
        return sc.set_brightness(int(m.group(1)))

    m = re.search(r'(?:open|launch|start)\s+(.+)', t)
    if m:
        app = m.group(1).strip()
        if len(app.split()) <= 3:
            return sc.open_app(app)

    m = re.search(r'(?:close|kill|terminate)\s+(.+)', t)
    if m:
        return sc.kill_process(m.group(1).strip())

    if any(w in t for w in ["shutdown", "shut down", "power off", "turn off the computer"]):
        return sc.shutdown(confirmed=True)

    if any(w in t for w in ["restart", "reboot"]):
        return sc.restart(confirmed=True)

    if any(w in t for w in ["cancel shutdown", "abort shutdown"]):
        return sc.cancel_shutdown()

    for keywords, handler in SYSTEM_COMMANDS:
        if any(kw in t for kw in keywords):
            return handler(t)

    return None


def print_banner():
    banner = f"""
{Fore.CYAN}╔═════════════════════════════════════════════╗
║     DEVILCORE — NOCTIS AI SYSTEM v0.2       ║
║     Neural Omniscient Cognitive             ║
║     Tactical Intelligence System            ║
╠═════════════════════════════════════════════╣
║  Commands:                                  ║
║   /forget  — Memory erased.                 ║
║   /model   — Invoke another form            ║
║   /code    — Switch to coding domain        ║
║   /chat    — Switch to chat domain          ║
║   /bye     — Return to the shadows.         ║
╚═════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def main():
    print_banner()

    from core.noctis_core import NoctisCore
    from config import NOCTIS_MODEL, CHAT_MODEL, NOCTIS_NAME, OWNER_NAME

    noctis = NoctisCore()
    print(f"{Fore.GREEN}[{NOCTIS_NAME}] Shadow network established. Awaiting orders, {OWNER_NAME}.{Style.RESET_ALL}\n")

    while True:
        try:
            user_input = input(f"{Fore.YELLOW}{OWNER_NAME}{Style.RESET_ALL} » ").strip()

            if not user_input:
                continue

            if user_input.lower() == '/bye':
                noctis.end_session()
                print(f"{Fore.CYAN}[{NOCTIS_NAME}] Session complete. Returning to the shadows.{Style.RESET_ALL}")
                break

            elif user_input.lower() == '/forget':
                noctis.clear_history()

            elif user_input.lower() == '/code':
                noctis.switch_model(NOCTIS_MODEL)
                print(f"{Fore.CYAN}[{NOCTIS_NAME}] Domain expansion: Code Sanctum.{Style.RESET_ALL}")

            elif user_input.lower() == '/chat':
                noctis.switch_model(CHAT_MODEL)
                print(f"{Fore.CYAN}[{NOCTIS_NAME}] Domain Expansion: Infinite Dialogue.{Style.RESET_ALL}")

            elif user_input.lower().startswith('/model '):
                model = user_input[7:].strip()
                noctis.switch_model(model)

            else:
                sys_result = match_system_command(user_input)
                if sys_result:
                    print(f"{Fore.CYAN}[{NOCTIS_NAME}]{Style.RESET_ALL} {sys_result}")
                else:
                    noctis.chat(user_input)

        except KeyboardInterrupt:
            noctis.end_session()
            print(f"\n{Fore.CYAN}[{NOCTIS_NAME}] Interrupted. Session closed.{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main()