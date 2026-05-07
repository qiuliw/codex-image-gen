#!/usr/bin/env python3
"""Convenience runner for the official Codex imagegen CLI.

This script does not implement image generation itself. It resolves credentials
from Codex config or one-off flags, then delegates to the bundled imagegen CLI.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HOME = Path.home()
CODEX_HOME = Path(os.environ.get("CODEX_HOME", HOME / ".codex"))
AUTH_PATH = CODEX_HOME / "auth.json"
CONFIG_PATH = CODEX_HOME / "config.toml"


def candidate_imagegen_paths() -> list[Path]:
    explicit = os.environ.get("CODEX_IMAGEGEN_CLI")
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(
        [
            CODEX_HOME / "skills/.system/imagegen/scripts/image_gen.py",
            CODEX_HOME / "skills/imagegen/scripts/image_gen.py",
            HOME / ".codex/skills/.system/imagegen/scripts/image_gen.py",
            HOME / ".codex/skills/imagegen/scripts/image_gen.py",
            HOME / ".agents/skills/imagegen/scripts/image_gen.py",
        ]
    )
    return candidates


def find_imagegen() -> Path:
    for candidate in candidate_imagegen_paths():
        if candidate.exists():
            return candidate
    tried = "\n".join(f"  - {path}" for path in candidate_imagegen_paths())
    raise SystemExit(
        "Official imagegen CLI was not found. Install or enable the official "
        "imagegen skill first, or set CODEX_IMAGEGEN_CLI to image_gen.py.\n"
        f"Checked:\n{tried}"
    )


def candidate_python_paths() -> list[Path]:
    candidates = []
    explicit = os.environ.get("CODEX_IMAGEGEN_PYTHON")
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(
        [
            HOME
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
            HOME
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
        ]
    )
    return candidates


def find_python() -> str:
    for candidate in candidate_python_paths():
        if candidate.exists():
            return str(candidate)
    return sys.executable


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url and not base_url.endswith("/v1"):
        base_url += "/v1"
    return base_url


def read_api_key(cli_api_key: str = "") -> str:
    if cli_api_key:
        return cli_api_key
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    try:
        data = json.loads(AUTH_PATH.read_text())
    except FileNotFoundError:
        raise SystemExit(
            "Missing OPENAI_API_KEY. Pass --api-key, export OPENAI_API_KEY, "
            f"or sign in so {AUTH_PATH} exists."
        )
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse {AUTH_PATH}: {exc}") from exc

    key = data.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit(
            f"{AUTH_PATH} does not contain OPENAI_API_KEY. "
            "Pass --api-key or export OPENAI_API_KEY."
        )
    return key


def read_base_url(cli_base_url: str = "") -> str:
    if cli_base_url:
        return normalize_base_url(cli_base_url)
    if os.environ.get("OPENAI_BASE_URL"):
        return normalize_base_url(os.environ["OPENAI_BASE_URL"])
    try:
        text = CONFIG_PATH.read_text()
    except FileNotFoundError:
        return ""

    provider_match = re.search(r'(?m)^model_provider\s*=\s*"([^"]+)"', text)
    provider = provider_match.group(1) if provider_match else ""
    if not provider:
        return ""

    section_re = re.compile(
        r'(?ms)^\[model_providers\.' + re.escape(provider) + r'\]\s*(.*?)(?=^\[|\Z)'
    )
    section_match = section_re.search(text)
    if not section_match:
        return ""

    base_match = re.search(r'(?m)^base_url\s*=\s*"([^"]+)"', section_match.group(1))
    return normalize_base_url(base_match.group(1)) if base_match else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run official Codex imagegen with Codex config credentials."
    )
    parser.add_argument(
        "--api-key",
        help="Use this API key for this run only. It is not written to disk.",
    )
    parser.add_argument(
        "--base-url",
        help="Use this OpenAI-compatible base URL for this run only.",
    )
    args, remaining = parser.parse_known_args()
    args.mode = "passthrough"
    args.passthrough = remaining

    if remaining[:1] == ["quick"]:
        quick = argparse.ArgumentParser(prog=f"{Path(sys.argv[0]).name} quick")
        quick.add_argument("prompt")
        quick.add_argument("--out", default="generated/image.png")
        quick.add_argument("--model", default="gpt-image-2")
        quick.add_argument("--size", default="auto")
        quick.add_argument("--quality", default="medium")
        quick.add_argument("--force", action="store_true")
        quick.add_argument("--dry-run", action="store_true")
        quick_args = quick.parse_args(remaining[1:])
        args.mode = "quick"
        args.prompt = quick_args.prompt
        args.out = quick_args.out
        args.model = quick_args.model
        args.size = quick_args.size
        args.quality = quick_args.quality
        args.force = quick_args.force
        args.dry_run = quick_args.dry_run
    return args


def imagegen_args(args: argparse.Namespace) -> list[str]:
    if args.mode == "quick":
        command = [
            "generate",
            "--prompt",
            args.prompt,
            "--out",
            args.out,
            "--model",
            args.model,
            "--size",
            args.size,
            "--quality",
            args.quality,
        ]
        if args.force:
            command.append("--force")
        if args.dry_run:
            command.append("--dry-run")
        return command
    return args.passthrough


def main() -> int:
    imagegen = find_imagegen()
    args = parse_args()
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = read_api_key(args.api_key or "")
    base_url = read_base_url(args.base_url or "")
    if base_url:
        env["OPENAI_BASE_URL"] = base_url

    return subprocess.call([find_python(), str(imagegen), *imagegen_args(args)], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
