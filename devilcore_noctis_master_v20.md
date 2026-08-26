# DEVILCORE / NOCTIS — MASTER PROMPT v20

**Owner**: DarkDevil
**Assistant name**: Noctis
**Hardware**: ARM64 (Acer Aspire 14 AI, Snapdragon X)
**Status**: Phase 8 finalized → entering Phase 9
**Toolchain constraint**: Free-tier only. No paid dependencies. Banned packages: PyTorch, PyAudio, `uvicorn[standard]`, and other previously-excluded packages per project rules.

---

## 1. CURRENT MODEL / INTELLIGENCE STATE

- Local models configured: `NOCTIS_MODEL=qwen2.5-coder:7b`, `NOCTIS_CHAT_MODEL=llama3.1:8b`
- **Chat/reasoning is currently routed to Groq cloud** (`llama-3.3-70b-versatile`), NOT local Ollama. This was an explicit, approved deviation from the local-only rule.
- Local Ollama first-token latency is unacceptably slow for interactive use:
  - `llama3.1:8b`: ~18.85s
  - `qwen2.5-coder:7b`: ~15.37s
- Groq 70B first-token latency: ~13.5s cold start, then ~0.1–0.5s per subsequent prompt.
- **Standing question for Phase 9+**: local-only is still the long-term goal per original project scope. Groq is a stopgap, not a final architecture decision. Revisit before any public-release build.

## 2. VOICE PIPELINE STATE

- VAD: Silero VAD via raw ONNX file (`voice/silero_vad.onnx`), running on `CPUExecutionProvider`. Thresholds: `silence_threshold=0.3`, `silence_duration=1.2`.
- STT: Whisper `large-v3`, with project-specific vocabulary hints injected via `voice/vocabulary_hints.py` (terms include DarkDevil, DevilCore, Noctis, Shadow-class, Snapdragon X, wake phrase "hey noctis", etc.)
- Mic capture: 16kHz, mono (1 channel).
- **UNTESTED — carry forward as open risk**: VAD silence/utterance accuracy, vocabulary hint effectiveness in live STT, mic truncation behavior. These were skipped for manual Tier 2 verification and have NOT been done. Do not assume they work just because unit tests pass.
- Legacy volume-gate logic (`np.abs(chunk).mean()`) still exists in `listen_for_wake_word()` inside `noctis_voice.py` — flagged for Phase 9 cleanup but NOT YET DONE.

## 3. KNOWN FIXED ISSUES (do not re-break)

- **UTF-8 crash**: Groq 70B output containing curly quotes/em-dashes caused `UnicodeEncodeError` under Windows' default `cp1252` code page, silently killing the hidden voice process. Fixed via `sys.stdout.reconfigure(encoding='utf-8')` in Python and `set PYTHONIOENCODING=utf-8` in `start_noctis.bat`. **Any new print/output path must preserve UTF-8 handling.**
- `stop_noctis.bat` was rewritten with `/T` tree-kill and WMI-based PowerShell sweeping to kill zombie orphaned `python.exe` processes. Do not revert to the simple version.

## 4. TEST SUITE STATUS

- `test_accuracy_deep.py`: 2/2 passing (vocabulary hint loading, case-insensitive command matching).
- `test_phase8_deep.py`: 6/6 passing (PID requirements, process tracking).
- **CAUTION**: `test_phase7_deep.py` was DELETED during Phase 8 cleanup, not fixed. Its original purpose was the Ollama-queue timeout fix. Passing `test_phase8_deep.py` covers process tracking, NOT the queue timeout issue. Treat the queue timeout as unconfirmed/unresolved unless separately verified.

## 5. NPU (HEXAGON) STATUS

- Current execution providers: `['AzureExecutionProvider', 'CPUExecutionProvider']` — no QNN provider active.
- `onnxruntime-qnn` is NOT installed and NOT investigated for Python 3.11.9 ARM64.
- All current ONNX workloads (VAD, vector store embedder) run on CPU; sub-millisecond execution was deemed sufficient — no NPU migration has occurred without explicit owner approval, and none should happen without it.

## 6. ENVIRONMENT SNAPSHOT

```
OLLAMA_HOST=http://localhost:11434
NOCTIS_MODEL=qwen2.5-coder:7b
NOCTIS_CHAT_MODEL=llama3.1:8b
NOCTIS_NAME=Noctis
OWNER_NAME=DarkDevil
LOG_PATH=C:/DevilCore/logs/noctis.log
GROQ_API_KEY=gsk_... (redacted)
MEMORY_SERVER_IP=100.74.202.92
```

New files as of Phase 8 close:
- `C:\DevilCore\voice\silero_vad.onnx`
- `C:\DevilCore\voice\vocabulary_hints.py`
- `C:\DevilCore\test_accuracy_deep.py`

Key packages: `groq` 1.4.0, `onnxruntime` 1.26.0, `sounddevice` 0.5.5. Note: `webrtcvad` failed to install; Silero is integrated via raw ONNX file instead — do not re-attempt `webrtcvad` without a reason to revisit.

## 7. PHASE 9 SCOPE (this phase)

**In scope:**
- Voice command OS-level control with passphrase-gated secure zones (Phase 8.5 carryover)
- Always-on system tray presence
- Boot launch
- Global hotkey

**Explicitly NOT in scope for Phase 9 (recommendations only, do not implement):**
- Rewriting `listen_for_wake_word()` to use Silero VAD instead of the legacy volume gate
- Compiling `onnxruntime-qnn` from source for ARM64 NPU acceleration

**Pre-Phase-9 recommendation**: run a manual smoke test of the voice loop (a handful of real utterances + silences) before adding OS-level surface area, since the voice pipeline's real-world behavior hasn't been human-verified since the Silero/Whisper changes landed.

## 8. UPCOMING / DEFERRED

- Split between private full-access build and public GitHub release with no pre-loaded memory — not yet started.
- Long-term architecture decision: Groq cloud vs. local-only for chat reasoning — currently on Groq, deviation is approved but not permanent.

---

**Standing convention**: as context limits approach, proactively output the next master prompt version (v21) capturing updated system state before continuing.
