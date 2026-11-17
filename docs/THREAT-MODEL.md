# Threat model

| Threat | Mitigation |
|---|---|
| Malicious prompt text attacks the scanner (ReDoS) | Bounded patterns, 50k chars per prompt, 500 prompts per call, body size cap |
| Prompt text attacks the optional LLM judge | Prompt wrapped as data, JSON-only reply, invalid verdict → review, judge never approves |
| Secrets leak via reports | Secret excerpts redacted in JSON, HTML, SARIF |
| XSS in the HTML report | Titles escaped client-side; embedded JSON escapes `</` |
| Data retention | Stateless; nothing stored; no egress at runtime (NetworkPolicy) |
| Supply chain | No runtime dependencies; distroless base; pinned upstream data commit |
| Over-trust in scores | Tiers are triage; docs and UI say it is not a sign-off; review tier for humans |
