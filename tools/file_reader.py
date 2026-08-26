import os
import sys

MAX_CHARS = 5000
SUPPORTED = [".txt", ".py", ".js", ".ts", ".json", ".md", ".yaml", ".yml",
             ".toml", ".ini", ".cfg", ".csv", ".html", ".css", ".xml", ".log"]


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _summarize_csv(content: str) -> str:
    lines = content.strip().splitlines()
    if not lines:
        return "[empty CSV]"
    header = lines[0]
    row_count = len(lines) - 1
    preview = "\n".join(lines[1:6])
    return f"Columns: {header}\nRows: {row_count}\nFirst 5 rows:\n{preview}"


def read_file(path: str, summarize: bool = False) -> str:
    path = os.path.normpath(path)

    if not os.path.exists(path):
        return f"[FileReader] ERROR — File not found: {path}"

    if os.path.isdir(path):
        entries = os.listdir(path)
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        dirs  = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        return (
            f"[FileReader] Directory: {path}\n"
            f"  Folders : {dirs}\n"
            f"  Files   : {files}"
        )

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED:
        return f"[FileReader] ERROR — Unsupported file type: {ext}"

    size = os.path.getsize(path)
    content = _read_text(path)

    if ext == ".csv" and summarize:
        body = _summarize_csv(content)
    elif len(content) > MAX_CHARS:
        body = content[:MAX_CHARS] + f"\n... [truncated — {len(content)} total chars]"
    else:
        body = content

    return (
        f"[FileReader] {os.path.basename(path)} ({size} bytes)\n"
        f"{'='*48}\n"
        f"{body}"
    )


def file_summary(path: str) -> str:
    return read_file(path, summarize=True)


if __name__ == "__main__":
    default_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.py")
    target = sys.argv[1] if len(sys.argv) > 1 else default_path
    print(read_file(target))
