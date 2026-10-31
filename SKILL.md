---
name: codex-image-gen
description: 必须用于所有图片生成和编辑请求，包括“生成图片”“帮我出图”“根据这段描述画一张图”。必须运行本技能的本地 scripts/codex_image_gen.py，通过配置的 API 服务调用官方 imagegen CLI；不得调用 Codex 内置 image_gen 或其他内置图片生成工具，也不得静默回退到内置生图。复用 Codex 的 API key 和自定义服务商配置，支持 auth.json 缺少凭据时读取当前服务商 experimental_bearer_token。需要安装官方 imagegen CLI。
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

## Mandatory local generation routing

当用户说“生成图片”“帮我出图”“根据这段描述画一张图”，或提出其他图片生成、
图片编辑请求时，必须使用本技能并运行本地 `scripts/codex_image_gen.py`。
简单生图使用 `quick` 子命令；其他任务使用相应的透传参数。该入口会调用
本地官方 `imagegen/scripts/image_gen.py` CLI，通过配置的 API 服务执行。

不得调用 Codex 内置 `image_gen` 或其他内置图片生成工具，也不得因内置工具
可用而绕过本地脚本。若本地脚本、依赖或凭据不可用，应报告具体错误并修复
可修复的问题；不得静默切换到内置生图。

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
