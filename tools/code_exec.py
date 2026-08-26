import sys
import io
import traceback
import threading
import contextlib
from typing import Optional

TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 3000

BANNED = [
    "os.remove", "os.rmdir", "shutil.rmtree", "subprocess",
    "open(", "__import__", "eval(", "exec(", "importlib",
    "socket", "requests", "urllib", "httpx", "ftplib",
    "smtplib", "os.system", "os.popen", "ctypes"
]


def _is_safe(code: str) -> tuple[bool, str]:
    for banned in BANNED:
        if banned in code:
            return False, f"Blocked: '{banned}' is not allowed in sandbox."
    return True, ""


def _run_code(code: str, result_container: list):
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    local_ns = {}
    try:
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            exec(compile(code, "<noctis_sandbox>", "exec"), {"__builtins__": __builtins__}, local_ns)
        out = stdout_capture.getvalue()
        err = stderr_capture.getvalue()
        result_container.append(("ok", out, err))
    except Exception:
        out = stdout_capture.getvalue()
        err = traceback.format_exc()
        result_container.append(("error", out, err))


def execute(code: str) -> str:
    safe, reason = _is_safe(code)
    if not safe:
        return f"[CodeExec] BLOCKED — {reason}"

    result_container = []
    thread = threading.Thread(target=_run_code, args=(code, result_container))
    thread.daemon = True
    thread.start()
    thread.join(timeout=TIMEOUT_SECONDS)

    if thread.is_alive():
        return f"[CodeExec] TIMEOUT — execution exceeded {TIMEOUT_SECONDS}s."

    status, out, err = result_container[0]
    output = ""
    if out:
        output += f"[Output]\n{out.strip()}"
    if err and status == "error":
        output += f"\n[Error]\n{err.strip()}"
    elif err:
        output += f"\n[Stderr]\n{err.strip()}"

    if not output:
        output = "[CodeExec] Executed — no output produced."

    return output[:MAX_OUTPUT_CHARS]


def execute_summary(code: str) -> str:
    result = execute(code)
    return f"[CodeExec] Code executed.\n{result}"


if __name__ == "__main__":
    test_code = """
import math
print('Pi is:', math.pi)
print('Square root of 2:', math.sqrt(2))
for i in range(5):
    print(f'  {i} squared = {i**2}')
"""
    print(execute(test_code))
