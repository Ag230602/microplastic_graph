#!/usr/bin/env python3
"""Local LLM proxy for the 10-paper dashboard.

Reads provider API keys from the local environment. Do not put API keys in the
dashboard HTML, JSON files, prompts, or chat.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from getpass import getpass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


HOST = "127.0.0.1"
PORT = int(os.environ.get("TEN_PAPER_LLM_PORT", "8765"))
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "auto")
GEMINI_MODEL_CACHE = ""


def active_provider() -> tuple[str, str, str]:
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")).strip()

    if provider == "openai" and openai_key:
        return "openai", OPENAI_MODEL, openai_key
    if provider in {"gemini", "google"} and gemini_key:
        return "gemini", GEMINI_MODEL, gemini_key
    if openai_key:
        return "openai", OPENAI_MODEL, openai_key
    if gemini_key:
        return "gemini", GEMINI_MODEL, gemini_key
    return "", "", ""


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            provider, model, api_key = active_provider()
            self._json({"ok": True, "provider": provider, "model": model, "has_api_key": bool(api_key)})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/llm":
            self.send_error(404, "Not found")
            return
        provider, model, api_key = active_provider()
        if not api_key:
            self._json({"ok": False, "error": "No API key is set. Use OPENAI_API_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY."}, 400)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            question = str(body.get("question", "")).strip()
            if not question:
                self._json({"ok": False, "error": "Missing question."}, 400)
                return
            if provider == "gemini":
                answer = call_gemini(api_key, question, model)
                model = GEMINI_MODEL_CACHE or model
            else:
                answer = call_openai(api_key, question, model)
            self._json({"ok": True, "provider": provider, "model": model, "answer": answer})
        except Exception as exc:  # noqa: BLE001 - returns local diagnostic only
            self._json({"ok": False, "error": str(exc)}, 500)

    def _json(self, payload: dict, status: int = 200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


SYSTEM_PROMPT = (
    "You are an independent scientific assistant. Answer the user's question about "
    "microplastics or nanoplastics in 1-2 concise paragraphs. Include uncertainty "
    "when evidence may be animal, in-vitro, or review-level. Do not invent citations."
)


def call_openai(api_key: str, question: str, model: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
    return data["choices"][0]["message"]["content"].strip()


def call_gemini(api_key: str, question: str, model: str) -> str:
    model = resolve_gemini_model(api_key, model)
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": question}]}],
        "generationConfig": {"temperature": 0.2},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {exc.code}: {detail}") from exc

    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini returned no text: {json.dumps(data)[:500]}")
    return text


def resolve_gemini_model(api_key: str, requested_model: str) -> str:
    global GEMINI_MODEL_CACHE
    if requested_model and requested_model != "auto":
        return requested_model
    if GEMINI_MODEL_CACHE:
        return GEMINI_MODEL_CACHE

    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini model discovery error {exc.code}: {detail}") from exc

    models = [
        model_info.get("name", "").replace("models/", "")
        for model_info in data.get("models", [])
        if "generateContent" in model_info.get("supportedGenerationMethods", [])
    ]
    preferred = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
    ]
    for name in preferred:
        if name in models:
            GEMINI_MODEL_CACHE = name
            return name
    for name in models:
        if "flash" in name:
            GEMINI_MODEL_CACHE = name
            return name
    if models:
        GEMINI_MODEL_CACHE = models[0]
        return models[0]
    raise RuntimeError("Gemini API returned no models that support generateContent.")


def main() -> int:
    provider, model, api_key = active_provider()
    if not api_key:
        print("No API key is set.")
        print("Paste ONLY a fresh OpenAI or Gemini key at the hidden prompt. Do not paste the prompt label.")
        api_key = getpass("New API key: ").strip()
        if not api_key:
            print("No key entered; exiting.")
            return 1
        if api_key.startswith("sk-"):
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            os.environ["GEMINI_API_KEY"] = api_key
        provider, model, _ = active_provider()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving dashboard and LLM proxy at http://{HOST}:{PORT}/")
    print(f"Using provider={provider or 'unknown'} model={model or 'unknown'}")
    print("Open http://127.0.0.1:8765/experiments/ten_paper_evidence_gated/ten_paper_dashboard.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    return 0


if __name__ == "__main__":
    sys.exit(main())