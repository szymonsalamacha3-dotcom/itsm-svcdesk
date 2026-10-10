---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai 1.2b0; openai 3.19.2; opentelemetry-sdk 1.45.0"
  spec_ref: "semantic-conventions-genai@e57c543b4889619eb2a05702471937db5119165d"
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 75% - Copilot compared the emitted span attributes with the pinned GenAI registry; the span was produced by a local instrumented model call -->

# GenAI instrumentation and conventions

The instrumented OpenAI-compatible chat call emitted eight `gen_ai.*` attributes, all present in the selected GenAI conventions snapshot and marked `development`. The request and response model names, operation, provider, finish reason, and token counts are useful fields for understanding a call and its resource use. The span also includes `server.address`, `server.port`, and `openai.response.system_fingerprint`; those are not `gen_ai.*` keys and are therefore outside the GenAI attribute set declared above.

The instrumentation did not emit message-content attributes for this call, so the recorded span avoids copying prompt and completion text into telemetry. The file exporter captures the attributes as OTLP JSON without requiring a collector, matching the lab's artifact format.
