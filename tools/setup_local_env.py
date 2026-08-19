from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update .env.local for local development secrets."
    )
    parser.add_argument(
        "--openai-api-key",
        default=None,
        help="Explicit OPENAI_API_KEY value to write into .env.local.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing keys in .env.local.",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt for missing values interactively.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'} and len(value) >= 2:
            value = value[1:-1]
        values[key] = value
    return values


def render_env_file(values: dict[str, str], ordered_keys: list[str]) -> str:
    lines = [
        "# Local development secrets for WNC Rental Brain.",
        "# This file is ignored by git.",
        "",
    ]
    for key in ordered_keys:
        lines.append(f"{key}={values.get(key, '')}")
    lines.append("")
    return "\n".join(lines)


def resolve_openai_api_key(args: argparse.Namespace, existing: dict[str, str]) -> str:
    explicit = args.openai_api_key
    if explicit is not None:
        return explicit.strip()

    current_env = os.environ.get("OPENAI_API_KEY")
    if current_env and current_env.strip():
        return current_env.strip()

    if existing.get("OPENAI_API_KEY") and not args.force:
        return existing["OPENAI_API_KEY"]

    if args.no_prompt:
        return existing.get("OPENAI_API_KEY", "")

    if not os.isatty(0):
        return existing.get("OPENAI_API_KEY", "")

    entered = getpass.getpass("Enter OPENAI_API_KEY for .env.local (leave blank to skip): ").strip()
    return entered or existing.get("OPENAI_API_KEY", "")


def main() -> int:
    args = parse_args()
    root = repo_root()
    example_path = root / ".env.example"
    target_path = root / ".env.local"

    template_values = parse_env_file(example_path)
    existing_values = parse_env_file(target_path)

    merged_values = template_values.copy()
    merged_values.update(existing_values)

    openai_api_key = resolve_openai_api_key(args, existing_values)
    if openai_api_key and (args.force or not merged_values.get("OPENAI_API_KEY")):
        merged_values["OPENAI_API_KEY"] = openai_api_key
    elif openai_api_key and args.force:
        merged_values["OPENAI_API_KEY"] = openai_api_key

    ordered_keys = list(template_values.keys())
    for key in merged_values:
        if key not in ordered_keys:
            ordered_keys.append(key)

    target_path.write_text(render_env_file(merged_values, ordered_keys), encoding="utf-8")

    masked = ""
    if merged_values.get("OPENAI_API_KEY"):
        key = merged_values["OPENAI_API_KEY"]
        masked = f"{key[:6]}...{key[-4:]}" if len(key) >= 10 else "[set]"

    print(f"wrote={target_path}")
    print(f"openai_api_key={'missing' if not merged_values.get('OPENAI_API_KEY') else masked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
