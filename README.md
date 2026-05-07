# codex-image-gen

`codex-image-gen` is a convenience skill for Codex users who want the official
`imagegen` CLI to reuse their existing Codex API key and custom provider
configuration.

It is intentionally thin:

- reads `OPENAI_API_KEY` from Codex auth when the shell does not have it
- reads the active Codex provider `base_url`
- normalizes custom providers to `/v1`
- delegates all image generation to the official Codex `imagegen` CLI

It does **not** copy or fork the official image generation implementation.

## Requirements

- Codex skills directory at `~/.codex/skills`
- Official system `imagegen` skill installed at:

  ```text
  ~/.codex/skills/.system/imagegen/scripts/image_gen.py
  ```

- Your provider must support the OpenAI-compatible Images API.

## Install

Clone or copy the skill folder into your Codex skills directory.

macOS/Linux default:

```bash
mkdir -p ~/.codex/skills
cp -R codex-image-gen ~/.codex/skills/codex-image-gen
```

Windows PowerShell default:

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
Copy-Item -Recurse .\codex-image-gen "$HOME\.codex\skills\codex-image-gen"
```

If installing from a GitHub checkout:

```bash
git clone https://github.com/<owner>/codex-image-gen.git
cp -R codex-image-gen/codex-image-gen ~/.codex/skills/codex-image-gen
```

## Quick Use

Generate with your existing Codex config:

```bash
python3 ~/.codex/skills/codex-image-gen/scripts/codex_image_gen.py \
  quick "a cute little fox, children's book illustration, warm colors" \
  --out fox.png \
  --force
```

Short helper:

```bash
~/.codex/skills/codex-image-gen/scripts/img \
  "a cute little fox, children's book illustration" \
  --out fox.png \
  --force
```

One-off API key and base URL, without editing shell config:

```bash
python3 ~/.codex/skills/codex-image-gen/scripts/codex_image_gen.py \
  --api-key "$OPENAI_API_KEY" \
  --base-url "https://router.example.com" \
  quick "a cute little fox" \
  --out fox.png \
  --force
```

Pass through official imagegen arguments:

```bash
python3 ~/.codex/skills/codex-image-gen/scripts/codex_image_gen.py \
  generate \
  --prompt "a cute little fox" \
  --out fox.png \
  --force
```

## How It Works

Credential resolution order:

1. `--api-key` and `--base-url`
2. `OPENAI_API_KEY` and `OPENAI_BASE_URL`
3. Codex files:
   - `~/.codex/auth.json`
   - `~/.codex/config.toml`

Then it runs:

```text
~/.codex/skills/.system/imagegen/scripts/image_gen.py
```

The official skill remains responsible for prompt handling, Images API calls,
output decoding, and file writing.

## Paths and Overrides

The script works across macOS, Linux, and Windows by using `Path.home()` and
environment variables instead of hardcoded user directories.

Defaults:

- Codex home: `$CODEX_HOME` if set, otherwise `~/.codex`
- Official imagegen:
  - `~/.codex/skills/.system/imagegen/scripts/image_gen.py`
  - `~/.codex/skills/imagegen/scripts/image_gen.py`
  - `~/.agents/skills/imagegen/scripts/image_gen.py`
- Python: current Python, unless a known Codex bundled Python exists

Optional overrides:

```bash
export CODEX_HOME="$HOME/.codex"
export CODEX_IMAGEGEN_CLI="$HOME/.codex/skills/.system/imagegen/scripts/image_gen.py"
export CODEX_IMAGEGEN_PYTHON="/path/to/python"
```

PowerShell:

```powershell
$env:CODEX_HOME = "$HOME\.codex"
$env:CODEX_IMAGEGEN_CLI = "$HOME\.codex\skills\.system\imagegen\scripts\image_gen.py"
$env:CODEX_IMAGEGEN_PYTHON = "C:\Path\To\python.exe"
```

## Troubleshooting

Use `--dry-run` to verify argument and credential wiring without generating:

```bash
python3 ~/.codex/skills/codex-image-gen/scripts/codex_image_gen.py \
  quick "test fox" \
  --out fox.png \
  --dry-run
```

If the official `imagegen` CLI is missing, install or enable the official
system `imagegen` skill first.
