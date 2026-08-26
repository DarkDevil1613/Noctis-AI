import re
import sys
from ddgs import DDGS
from bs4 import BeautifulSoup
import requests

MAX_RESULTS = 2
FETCH_TIMEOUT = 6
MAX_BODY_CHARS = 2000


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_body(url: str) -> str:
    try:
        r = requests.get(url, timeout=FETCH_TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
            return _clean_html(r.text)[:MAX_BODY_CHARS]
    except Exception:
        pass
    return ""


def search(query: str, fetch_body: bool = False) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(
                query,
                max_results=MAX_RESULTS,
                region="us-en",
                safesearch="off",
                timeout=8
            ))
        for r in raw:
            entry = {
                "title":   r.get("title", ""),
                "url":     r.get("href",  ""),
                "snippet": r.get("body",  ""),
                "body":    ""
            }
            if fetch_body and entry["url"]:
                entry["body"] = _fetch_body(entry["url"])
            results.append(entry)
    except Exception as e:
        results = [{"title": "ERROR", "url": "", "snippet": str(e), "body": ""}]
    return results


def search_summary(query: str, fetch_body: bool = False) -> str:
    results = search(query, fetch_body=fetch_body)
    if not results:
        return "[WebSearch] No results found."

    lines = [f"[WebSearch] Query: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"  [{i}] {r['title']}")
        lines.append(f"      URL: {r['url']}")
        lines.append(f"      {r['snippet']}")
        if r["body"]:
            lines.append(f"      --- Page excerpt ---")
            lines.append(f"      {r['body'][:800]}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "ollama latest version"
    print(search_summary(q, fetch_body=False))
