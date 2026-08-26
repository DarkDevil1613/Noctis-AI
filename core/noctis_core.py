import time
import requests
import json
import sys
import os
import threading
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import OLLAMA_HOST, CHAT_MODEL, SYSTEM_PROMPT, NOCTIS_NAME, OWNER_NAME, MEMORY_SERVER_IP
from datetime import datetime
from memory.db import (
            init_db, start_session, end_session,
            log_message, save_fact, get_all_facts,
            save_preference, get_all_preferences,
            sync_offline_to_server
        )
# ── Memory Imports ────────────────────────────────────────────────────────────────────────────────────────
try:
    from memory.db import (
        init_db, start_session, end_session,
        log_message, save_fact, get_all_facts,
        save_preference, get_all_preferences
    )
    from memory.logger import NoctisLogger
    from memory.vector_store import NoctisVectorStore
    MEMORY_AVAILABLE = True
except Exception as e:
    print(f"[{NOCTIS_NAME}] WARNING: Memory system failed to load — {e}")
    MEMORY_AVAILABLE = False

# ── Tool Router ───────────────────────────────────────────────────────────────────────────────────────────
try:
    from tools.tool_router import route as tool_route
    TOOLS_AVAILABLE = True
except Exception as e:
    print(f"[{NOCTIS_NAME}] WARNING: Tool router failed to load — {e}")
    TOOLS_AVAILABLE = False


try:
    from tools.system_control import SystemControl
    SYS_CONTROL_AVAILABLE = True
except Exception:
    SYS_CONTROL_AVAILABLE = False


class NoctisCore:
    def __init__(self):
        self.model = CHAT_MODEL
        self.sc = SystemControl() if SYS_CONTROL_AVAILABLE else None
        self.conversation_history = []
        self.session_start = datetime.now()
        self.system_prompt = SYSTEM_PROMPT
        self.session_id = None
        self._lock = threading.Lock()  # thread safety for concurrent API calls
        self._llm_lock = threading.Lock()
        self._last_call_time = 0.0
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # ── Init Memory ──────────────────────────────────────────────────────────────────────────────────
        if MEMORY_AVAILABLE:
            try:
                init_db()
                self.logger = NoctisLogger()
                self.vector_store = NoctisVectorStore()
                self.vector_store.sync_offline_cache()
                sync_offline_to_server()
                self.session_id = start_session()
                self._seed_core_facts()
                print(f"[{NOCTIS_NAME}] Memory online. Session ID: {self.session_id}")
            except Exception as e:
                print(f"[{NOCTIS_NAME}] WARNING: Memory init failed — {e}")
                self.logger = None
                self.vector_store = None
        else:
            self.logger = None
            self.vector_store = None

        self._verify_ollama()

    def _seed_core_facts(self):
        if self.vector_store is None or self.vector_store.count() > 0:
            return
        core_facts = [
            "DarkDevil is the owner and creator of Noctis and the DevilCore project.",
            "DarkDevil uses an Acer Aspire 14 AI with Windows 11 ARM64 and Snapdragon X.",
            "DarkDevil prefers dark themes, minimal UI, and anime villain aesthetics.",
            "DarkDevil's AI is named Noctis — Shadow-class, loyal only to DarkDevil.",
            "The DevilCore project runs locally on ARM64 with Ollama for inference.",
            "Noctis uses Groq Whisper large-v3 for speech to text.",
            f"DarkDevil's memory server is a Linux PC at Tailscale IP {MEMORY_SERVER_IP}.",
            "DarkDevil prefers precise answers — no filler, no apology, no diplomacy.",
        ]
        for fact in core_facts:
            self.vector_store.add(fact, {"type": "core_fact"})
        print(f"[{NOCTIS_NAME}] Core facts seeded into vector store.")

    def _build_memory_context(self, user_message: str) -> str:
        if self.vector_store is None:
            return ""
        context_parts = []

        vector_context = self.vector_store.build_context(user_message, top_k=2)
        if vector_context:
            context_parts.append(vector_context)

        try:
            facts = get_all_facts()
            if facts:
                items = list(facts.items())[-5:]
                lines = ["[Stored Facts]"]
                for key, value in items:
                    lines.append(f"- {key}: {value}")
                context_parts.append("\n".join(lines))
        except Exception:
            pass

        return "\n\n".join(context_parts)

    def _verify_ollama(self):
        if not OLLAMA_HOST:
            print(f"[{NOCTIS_NAME}] Inference Engine: Groq Cloud API (Standalone)")
            return
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m['name'] for m in r.json().get('models', [])]
                print(f"[{NOCTIS_NAME}] Local Ollama Engine Online ({OLLAMA_HOST}). Models: {', '.join(models)}")
            else:
                print(f"[{NOCTIS_NAME}] Ollama status: {r.status_code}. Defaulting to Groq Cloud API.")
        except Exception:
            print(f"[{NOCTIS_NAME}] Inference Engine: Groq Cloud API (Standalone)")

    def _auto_select_model(self, user_message: str):
        msg = user_message.lower()
        coding_keywords = [
            "code", "script", "function", "bug", "error", "fix", "python",
            "javascript", "class", "import", "def ", "loop", "array",
            "debug", "compile", "syntax", "algorithm", "program", "write a"
        ]
        heavy_keywords = [
            "explain in detail", "analyze", "compare", "summarize",
            "write an essay", "full report", "deep dive", "pros and cons",
            "philosophy", "theory", "research"
        ]

        is_coding = any(k in msg for k in coding_keywords)
        is_heavy  = any(k in msg for k in heavy_keywords)

        from config import NOCTIS_MODEL, CHAT_MODEL
        if is_coding:
            target = NOCTIS_MODEL
        elif is_heavy:
            target = "llama3.2:3b"
        else:
            target = "llama3.2:3b"

        if self.model != target:
            self.model = target
            print(f"[Noctis] Model -> {target}")

    def _extract_and_store_preferences(self, text: str):
        import re
        matches = re.findall(r'@(.+?)@', text)
        for match in matches:
            match = match.strip()
            if not match:
                continue
            if match.lower().startswith("delete "):
                key = match[7:].strip().lower().replace(" ", "_")
                try:
                    from memory.db import delete_preference
                    delete_preference(key)
                    print(f"[Noctis] Preference deleted — {key}")
                    self._update_config_preferences()
                except Exception as e:
                    print(f"[Noctis] Delete preference failed — {e}")
            else:
                key = match[:50].lower().replace(" ", "_").replace("'", "")
                value = match
                try:
                    from memory.db import save_preference
                    save_preference(key, value)
                    if self.vector_store:
                        self.vector_store.add(
                            f"DarkDevil preference: {value}",
                            {"type": "preference", "key": key}
                        )
                    print(f"[Noctis] Preference stored — {value}")
                    self._update_config_preferences()
                except Exception as e:
                    print(f"[Noctis] Store preference failed — {e}")

    def _update_config_preferences(self):
        try:
            from memory.db import get_all_preferences
            prefs = get_all_preferences()
            if not prefs:
                return
            pref_block = "\n".join([f"- {v}" for v in prefs.values()])
            updated_prompt = (
                self.system_prompt.split("═══════════════════════════════════════\nLIVE PREFERENCES")[0].rstrip()
                + f"\n\n═══════════════════════════════════════\nLIVE PREFERENCES — ALWAYS FOLLOW\n═══════════════════════════════════════\n{pref_block}"
            )
            self.system_prompt = updated_prompt
            print(f"[Noctis] System prompt updated with {len(prefs)} preferences.")
        except Exception as e:
            print(f"[Noctis] Prompt update failed — {e}")

    def chat(self, user_message: str, stream: bool = True) -> str:
        # Check system control commands first (volume, brightness, open folders, web search, etc.)
        if self.sc:
            sys_res = self.sc.execute_command(user_message)
            if sys_res:
                safe_preview = sys_res[:100].encode('ascii', 'replace').decode('ascii').replace('\n', ' ')
                print(f"[{NOCTIS_NAME}] System command executed: {safe_preview}")
                return sys_res

        self._auto_select_model(user_message)

        tool_inject = ""
        if TOOLS_AVAILABLE:
            try:
                tool_result = tool_route(user_message)
                if tool_result["tool"] != "none":
                    tool_inject = tool_result["inject"]
                    print(f"[{NOCTIS_NAME}] Tool used: {tool_result['tool']}")
            except Exception as e:
                print(f"[{NOCTIS_NAME}] Tool routing error — {e}")

        self._extract_and_store_preferences(user_message)

        if tool_inject:
            enriched_message = (
                f"{user_message}\n\n"
                f"[Context from tools — use this to answer. CRITICAL: respond as Noctis in your natural voice. "
                f"Never mention 'web search results', 'provided context', 'extracted information', or any reference "
                f"to tools. Never say you are ready to assist. Just answer directly and stop.]\n"
                f"{tool_inject[:800]}"
            )
        else:
            enriched_message = user_message

        with self._lock:
            self.conversation_history.append({"role": "user", "content": enriched_message})
            history_snapshot = list(self.conversation_history)
            current_model = self.model

        if self.logger and self.session_id:
            try:
                self.logger.log(f"[USER] {user_message}")
                log_message(self.session_id, "user", user_message)
            except Exception:
                pass

        memory_context = self._build_memory_context(user_message)
        if memory_context:
            active_system_prompt = self.system_prompt + "\n\n" + memory_context
        else:
            active_system_prompt = self.system_prompt

        payload = {
            "model": current_model,
            "messages": [
                {"role": "system", "content": active_system_prompt}
            ] + history_snapshot,
            "stream": stream
        }

        try:
            with self._llm_lock:
                messages = [{"role": "system", "content": active_system_prompt}] + history_snapshot
                
                response = self.groq_client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=messages,
                    stream=stream,
                    temperature=0.7
                )

                full_response = ""

                if stream:
                    print(f"\n{NOCTIS_NAME}: ", end="", flush=True)
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            print(content, end="", flush=True)
                            full_response += content
                    print()
                else:
                    full_response = response.choices[0].message.content
                    
                self._last_call_time = time.time()

            with self._lock:
                self.conversation_history.append({"role": "assistant", "content": full_response})
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

            if self.logger and self.session_id:
                try:
                    self.logger.log(f"[NOCTIS] {full_response}")
                    log_message(self.session_id, "assistant", full_response)
                except Exception:
                    pass

            if self.vector_store:
                try:
                    self.vector_store.add(
                        f"User: {user_message} | Noctis: {full_response[:200]}",
                        {"type": "conversation", "session_id": str(self.session_id)}
                    )
                except Exception:
                    pass

            return full_response

        except requests.exceptions.Timeout:
            msg = "Response timed out. The model may be loading — try again."
            print(f"\n[{NOCTIS_NAME}] {msg}")
            return msg
        except Exception as e:
            msg = f"Error communicating with Groq: {e}"
            print(f"\n[{NOCTIS_NAME}] {msg}")
            return msg

    def chat_stream(self, user_message: str):
        """Generator yielding string tokens as they arrive from Groq."""
        if self.sc:
            sys_res = self.sc.execute_command(user_message)
            if sys_res:
                yield sys_res
                return

        self._auto_select_model(user_message)
        tool_inject = ""
        if TOOLS_AVAILABLE:
            try:
                tool_result = tool_route(user_message)
                if tool_result["tool"] != "none":
                    tool_inject = tool_result["inject"]
            except Exception:
                pass

        if tool_inject:
            enriched_message = (
                f"{user_message}\n\n"
                f"[Context from tools — use this to answer. CRITICAL: respond as Noctis in your natural voice. "
                f"Never mention 'web search results' or tools. Answer directly.]\n"
                f"{tool_inject[:800]}"
            )
        else:
            enriched_message = user_message

        with self._lock:
            self.conversation_history.append({"role": "user", "content": enriched_message})
            history_snapshot = list(self.conversation_history)

        memory_context = self._build_memory_context(user_message)
        active_system_prompt = (self.system_prompt + "\n\n" + memory_context) if memory_context else self.system_prompt
        messages = [{"role": "system", "content": active_system_prompt}] + history_snapshot

        full_response = ""
        try:
            with self._llm_lock:
                response = self.groq_client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=messages,
                    stream=True,
                    temperature=0.7
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        yield content

            with self._lock:
                self.conversation_history.append({"role": "assistant", "content": full_response})
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
        except Exception as e:
            yield f"[Error: {e}]"

    def clear_history(self):
        self.conversation_history = []
        print(f"[{NOCTIS_NAME}] Memory wiped.")

    def switch_model(self, model_name: str):
        self.model = model_name
        print(f"[{NOCTIS_NAME}] Switched to model: {model_name}")

    def remember_fact(self, key: str, value: str):
        try:
            save_fact(key, value)
        except Exception:
            pass
        if self.vector_store:
            try:
                self.vector_store.add(f"{key}: {value}", {"type": "fact", "key": key})
            except Exception:
                pass
        print(f"[{NOCTIS_NAME}] Fact stored — {key}: {value}")

    def remember_preference(self, key: str, value: str):
        try:
            save_preference(key, value)
        except Exception:
            pass
        if self.vector_store:
            try:
                self.vector_store.add(
                    f"DarkDevil preference — {key}: {value}",
                    {"type": "preference", "key": key}
                )
            except Exception:
                pass
        print(f"[{NOCTIS_NAME}] Preference stored — {key}: {value}")

    def end_session(self):
        if self.session_id:
            try:
                end_session(self.session_id)
                print(f"[{NOCTIS_NAME}] Session {self.session_id} closed.")
            except Exception:
                pass
        if self.logger:
            try:
                self.logger.log("=== SESSION END ===")
            except Exception:
                pass