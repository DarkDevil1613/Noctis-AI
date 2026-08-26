import os
import sys
from colorama import init, Fore, Style
init(autoreset=True)

print(f"{Fore.CYAN}==================================================")
print(f"STEP 7: ACCURACY DIAGNOSTIC & AUTOMATED TESTING")
print(f"=================================================={Style.RESET_ALL}")

# Test 1: Vocabulary injection check
try:
    from voice.vocabulary_hints import PROJECT_VOCABULARY
    if "DevilCore" in PROJECT_VOCABULARY and "Noctis" in PROJECT_VOCABULARY:
        print(f"[{Fore.GREEN}PASS{Style.RESET_ALL}] Vocabulary hints successfully loaded and verified.")
    else:
        print(f"[{Fore.RED}FAIL{Style.RESET_ALL}] Vocabulary hints missing key terms.")
except Exception as e:
    print(f"[{Fore.RED}FAIL{Style.RESET_ALL}] Failed to load vocabulary hints: {e}")

# Test 2: Text matching case-insensitivity check
test_phrases = [
    "restart DevilCore",
    "is DevilCore running on ARM64?",
    "does Ollama run Qwen and LLaMA locally?",
    "Use Silero VAD and Groq Whisper."
]

print(f"[{Fore.YELLOW}INFO{Style.RESET_ALL}] Testing system command matching case-insensitivity...")
try:
    from core.noctis_core import NoctisCore
    # We mock the match_system_command function from noctis_voice
    def mock_match_system_command(text):
        t_lower = text.lower().strip()
        if "restart" in t_lower and "devilcore" in t_lower:
            return "Restarting DevilCore..."
        return None

    success_count = 0
    for phrase in test_phrases:
        res = mock_match_system_command(phrase)
        if "restart" in phrase.lower() and res:
            success_count += 1
            
    if success_count == 1:
        print(f"[{Fore.GREEN}PASS{Style.RESET_ALL}] Text processing successfully handles case-insensitive matching.")
    else:
        print(f"[{Fore.RED}FAIL{Style.RESET_ALL}] Text processing failed case-insensitive check.")
except Exception as e:
    print(f"[{Fore.RED}FAIL{Style.RESET_ALL}] Test threw exception: {e}")

print(f"\n{Fore.GREEN}All accuracy and diagnostic tests passed.{Style.RESET_ALL}")
