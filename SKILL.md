---
name: codex-image-gen
description: Generate images through the official Codex imagegen CLI while reusing Codex auth and custom provider configuration. Use when the user wants quick image generation, wants imagegen to work with their current Codex OPENAI_API_KEY/base_url setup, or wants one-off --api-key/--base-url image generation without editing shell configuration. This skill is a thin wrapper over the official imagegen skill and requires that official imagegen is installed.
---

# codex-image-gen

Use this skill when the user wants convenient image generation through the
official Codex `imagegen` CLI, especially when their API key and custom provider
are already configured in Codex rather than exported in the shell.

This skill does not implement image generation and does not copy official
`imagegen` internals. It sets `OPENAI_API_KEY` and `OPENAI_BASE_URL`, then
delegates to:

```bash
~/.codex/skills/.system/imagegen/scripts/image_gen.py
```

## Quick Workflow

1. Ask for the image prompt if the user has not provided one.
2. Prefer the short helper for simple text-to-image generation:
   ```bash
   python3 <skill-dir>/scripts/codex_image_gen.py quick "<prompt>" --out <path> --force
   ```
3. For advanced `imagegen` options, pass through official arguments:
   ```bash
   python3 <skill-dir>/scripts/codex_image_gen.py generate --prompt "<prompt>" --out <path> --force
   ```
4. For one-off credentials without changing shell config:
   ```bash
   python3 <skill-dir>/scripts/codex_image_gen.py \
     --api-key "$KEY" \
     --base-url "https://router.example.com" \
     quick "<prompt>" \
     --out <path> \
     --force
   ```
5. Verify the output file exists and report the saved path.

## Credential Resolution

The wrapper resolves credentials in this order:

1. `--api-key` / `--base-url` flags for this run only.
2. Existing `OPENAI_API_KEY` / `OPENAI_BASE_URL` environment variables.
3. Codex config:
   - `~/.codex/auth.json` for `OPENAI_API_KEY`
   - `~/.codex/config.toml` for the active provider `base_url`

If the Codex provider `base_url` does not end in `/v1`, the wrapper appends
`/v1` for OpenAI SDK compatibility.

## Paths

The wrapper is cross-platform. It uses `CODEX_HOME` when set, otherwise
`Path.home() / ".codex"`.

If the official `imagegen` skill is installed somewhere unusual, set:

```bash
CODEX_IMAGEGEN_CLI=/path/to/image_gen.py
```

If a specific Python interpreter is needed, set:

```bash
CODEX_IMAGEGEN_PYTHON=/path/to/python
```

## Missing Official imagegen

If the official imagegen CLI is missing, stop and tell the user to install or
enable the official `imagegen` skill. Do not copy the official implementation
into this skill.

## Notes

- Keep prompts concise but specific: subject, style, composition, and output use.
- Use `--dry-run` before a real call when debugging provider configuration.
- If a real call fails with a network error, retry only after checking whether
  the environment needs network approval or proxy access.

## Credential fallback

API key precedence: `--api-key`, `OPENAI_API_KEY` environment variable,
`OPENAI_API_KEY` in `auth.json`, then the active provider's
`experimental_bearer_token` in `config.toml` (Python 3.11+ for TOML fallback).
The fallback applies when `auth.json` is absent or its API key is missing,
null, empty, or whitespace-only. Only the provider selected by `model_provider`
is used; tokens from other providers are ignored. Malformed credential files
raise an error. Credentials are not printed or persisted.
