#!/usr/bin/env python3
import time
import os
import sys
import json

# Añadir el directorio actual al path para importar chat_with_llm
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from chat_with_llm import chat_openai, chat_anthropic, chat_gemini, chat_groq, chat_openrouter
except ImportError:
    print("Error: No se pudo importar chat_with_llm.py", file=sys.stderr)
    sys.exit(1)


def measure_latency(provider_name, chat_function, model_name):
    print(f"⏳ Probando {provider_name} ({model_name})...", end="", flush=True)

    messages = [{"role": "user", "content": "Responde solo con la palabra 'Pong'."}]

    start_time = time.time()
    response = chat_function(messages, model=model_name)
    end_time = time.time()

    duration = end_time - start_time

    if "error" in response:
        print(f" ❌ Error: {response['error']}")
        return None
    else:
        print(f" ✅ {duration:.2f}s")
        return duration


def main():
    print("\n🏎️  INICIANDO BENCHMARK DE MODELOS LLM")
    print("========================================")

    results = []

    # 0. OpenRouter (créditos propios)
    if os.getenv("OPENROUTER_API_KEY"):
        t = measure_latency("OpenRouter", chat_openrouter, "google/gemini-3.7-flash")
        if t:
            results.append(("OpenRouter (Gemini Flash)", t))
    else:
        print("⚪ OpenRouter: Skipped (No API Key)")

    # 1. Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        t = measure_latency("Google", chat_gemini, "gemini-flash-latest")
        if t:
            results.append(("Gemini (Flash)", t))
    else:
        print("⚪ Google: Skipped (No API Key)")

    # 2. OpenAI
    if os.getenv("OPENAI_API_KEY"):
        t = measure_latency("OpenAI", chat_openai, "gpt-4o-mini")
        if t:
            results.append(("OpenAI (GPT-4o-mini)", t))
    else:
        print("⚪ OpenAI: Skipped (No API Key)")

    # 3. Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        t = measure_latency("Anthropic", chat_anthropic, "claude-3-5-sonnet")
        if t:
            results.append(("Anthropic (Sonnet)", t))
    else:
        print("⚪ Anthropic: Skipped (No API Key)")

    # 4. Groq
    if os.getenv("GROQ_API_KEY"):
        t = measure_latency("Groq", chat_groq, "llama-3.3-70b-versatile")
        if t:
            results.append(("Groq (Llama 3)", t))
    else:
        print("⚪ Groq: Skipped (No API Key)")

    print("\n📊 RESULTADOS FINALES (Menor es mejor)")
    print("----------------------------------------")
    for name, duration in sorted(results, key=lambda x: x[1]):
        print(f"{name:<25} | {duration:.4f} s")


if __name__ == "__main__":
    main()
