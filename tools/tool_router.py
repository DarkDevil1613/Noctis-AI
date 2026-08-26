import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.web_search import search_summary
from tools.code_exec import execute
from tools.file_reader import read_file
WEB_PATTERNS = [
    r"\b(search for|look up|google|find info|latest news|current price|what is the latest|who is the current|release date|version number)\b",
    r"\b(when did|when was).{5,}(happen|release|launch|born|die|start|end|come out)\b",
    r"\b(how much does|how many are|where is located|is there a)\b.{5,}",
] 
CODE_PATTERNS = [
    r"\b(run|execute|compute|calculate|eval|output|result of|what does this (code|script) do)\b",
    r"\b(python|script|function|loop|algorithm)\b.*\b(run|execute|output|result)\b",
]

FILE_PATTERNS = [
    r"(C:\\|N:\\|\.py|\.txt|\.json|\.csv|\.log|\.md|\.yaml|\.yml|\.toml|\.cfg|\.ini)[\w\\\.\-]+",
    r"\b(read|open|show|load|summarize|check)\b.{0,40}\b(file|folder|directory|path|log)\b",
]


def _match(text, patterns):
    text_lower = text.lower()
    for p in patterns:
        if re.search(p, text_lower, re.IGNORECASE):
            return True
    return False


def _extract_path(text):
    match = re.search(
        r"([A-Za-z]:\\[\w\\\.\-]+|N:\\[\w\\\.\-]+)",
        text
    )
    return match.group(0) if match else None


def _extract_code(text):
    match = re.search(r"```(?:python)?\s*([\s\S]+?)```", text)
    return match.group(1).strip() if match else None


def _clean_query(text):
    text = re.sub(r"(hey noctis|noctis|please|can you|could you|i want to know)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def route(user_input):
    code = _extract_code(user_input)
    if code and _match(user_input, CODE_PATTERNS):
        result = execute(code)
        return {
            "tool"  : "code",
            "result": result,
            "inject": f"[Tool: CodeExec]\n{result}"
        }

    path = _extract_path(user_input)
    if path and _match(user_input, FILE_PATTERNS):
        result = read_file(path)
        return {
            "tool"  : "file",
            "result": result,
            "inject": f"[Tool: FileReader]\n{result}"
        }

    SOCIAL_PHRASES = [
        "how are you", "how do you feel", "are you okay",
        "what's up", "whats up", "how have you been",
        "good morning", "good night", "hello", "hi noctis",
        "what do you think", "tell me about yourself", "who are you",
        "what can you do", "what are you", "talk to me",
        "what is your", "how do you", "do you have",
        "can you help", "i want to", "let's talk",
        "what's your", "whats your", "explain to me",
        "help me", "i need", "i have a"
    ]
    is_social = any(p in user_input.lower() for p in SOCIAL_PHRASES)

    if _match(user_input, WEB_PATTERNS) and not is_social:
        query = _clean_query(user_input)
        result = search_summary(query)
        return {
            "tool"  : "web",
            "result": result,
            "inject": f"[Tool: WebSearch]\n{result}"
        }

    return {"tool": "none", "result": "", "inject": ""}


if __name__ == "__main__":
    tests = [
        "what is the latest python version",
        "read the file C:\\DevilCore\\config.py",
        "how are you doing today",
    ]
    for t in tests:
        r = route(t)
        print(f"INPUT : {t}")
        print(f"TOOL  : {r['tool']}")
        print(f"RESULT: {r['result'][:120] if r['result'] else 'none'}")
        print("-" * 60)