# Security Policy

## Scope

AI Text Detector runs **locally** and does not require sending user text to any
third-party API for its core detection. It does, however, download model weights
(GPT-2, and optionally RoBERTa) from the Hugging Face Hub on first use.

## Supported versions

Security fixes target the latest `main`. There is no long-term-support branch.

## Model / supply-chain safety

- Model weights are loaded with `use_safetensors=True`, which avoids Python
  pickle deserialization (a known remote-code-execution class in `torch.load`).
- Dependency floors are set to patched releases (`torch>=2.6`,
  `transformers>=4.48`). Keep dependencies updated; run `pip list --outdated`.
- For high-assurance environments, pin a specific Hub revision via
  `GPT2Config.revision` / `RoBERTaConfig.revision` (a commit hash) so weights are
  reproducible and cannot silently change.

## Deploying beyond localhost

The Streamlit apps are designed for local, single-user use. If you expose them
on a network, you are responsible for adding:

- an input size cap (very long input increases GPU/CPU time), and
- authentication / rate limiting, and
- generic user-facing error messages (avoid surfacing raw exception strings).

## Reporting a vulnerability

Please report suspected vulnerabilities privately to
**shivamsatyam35@gmail.com** rather than opening a public issue. Include steps
to reproduce and any relevant logs. You can expect an initial response within a
reasonable time frame; please allow time for a fix before public disclosure.
