import os
import sys
import time
import requests
from dotenv import load_dotenv
from groq import Groq
import onnxruntime as ort
import subprocess

load_dotenv("C:/DevilCore/.env")

print("--- SECTION 1 ---")
# Prompts for testing
prompts = [
    "Hello",
    "What is DevilCore?",
    "Does Ollama run locally?",
    "Explain ARM64 architecture briefly.",
    "What is Tailscale used for?",
    "Write a hello world in Python.",
    "What is the capital of France?",
    "Who created Linux?",
    "What is ONNX?",
    "Count from 1 to 5."
]

print("Groq Test:")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
for p in prompts:
    start = time.time()
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user", "content":p}],
            stream=True
        )
        first_token = False
        full_text = ""
        for chunk in res:
            content = chunk.choices[0].delta.content
            if content:
                if not first_token:
                    latency = time.time() - start
                    print(f"[{p}] Latency: {latency:.4f}s")
                    first_token = True
                full_text += content
        print(f"[{p}] Response: {full_text.strip()}")
    except Exception as e:
        print(f"[{p}] Failed: {e}")

print("Ollama Test (llama3.1:8b):")
for p in prompts:
    start = time.time()
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.1:8b", "prompt": p, "stream": True},
            stream=True,
            timeout=30
        )
        first_token = False
        full_text = ""
        for line in res.iter_lines():
            if line:
                data = requests.models.json.loads(line)
                content = data.get("response", "")
                if content:
                    if not first_token:
                        latency = time.time() - start
                        print(f"[{p}] Latency: {latency:.4f}s")
                        first_token = True
                    full_text += content
                if data.get("done"):
                    break
        print(f"[{p}] Response: {full_text.strip()}")
    except Exception as e:
        print(f"[{p}] Failed: {e}")

print("--- SECTION 5 ---")
print("Providers:", ort.get_available_providers())

print("--- SECTION 6 ---")
print("PIP LIST:")
subprocess.run("venv\\Scripts\\pip list | findstr /I \"onnx groq sounddevice webrtcvad silero\"", shell=True)
