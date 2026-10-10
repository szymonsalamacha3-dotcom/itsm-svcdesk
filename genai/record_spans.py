# ai-generated: 90% - Copilot wrote the one-off local instrumented call driver from the Lab 3 handout
from __future__ import annotations

import os

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.exporter.otlp.json.file import FileSpanExporter
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


def main() -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(FileSpanExporter("genai/spans.json")))
    trace.set_tracer_provider(provider)
    OpenAIInstrumentor().instrument(tracer_provider=provider)

    client = OpenAI(
        api_key=os.getenv("GENAI_API_KEY", "ollama"),
        base_url=os.getenv("GENAI_BASE_URL", "http://localhost:11434/v1"),
    )
    try:
        result = client.chat.completions.create(
            model=os.getenv("GENAI_MODEL", "qwen3:1.7b"),
            messages=[{"role": "user", "content": "Reply with one word: ready."}],
        )
        print(result.model)
    finally:
        provider.shutdown()


if __name__ == "__main__":
    main()