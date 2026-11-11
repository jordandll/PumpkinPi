from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_EXCLUDED_FILES = {"__init__.py", "__main__.py", "cli.py"}


def _discover_scripts() -> dict[str, Path]:
    package_dir = Path(__file__).resolve().parent
    return {
        path.stem: path
        for path in package_dir.iterdir()
        if path.is_file() and path.suffix == ".py" and path.name not in _EXCLUDED_FILES
    }


def _build_help() -> str:
    scripts = sorted(_discover_scripts())
    lines = [
        "Usage: pumpkinpi <subcommand> [options]",
        "",
        "Run a PumpkinPi script by name.",
        "",
        "Available subcommands:",
    ]
    if scripts:
        lines.extend(f"  {name}" for name in scripts)
    else:
        lines.append("  (none)")
    lines.extend([
        "",
        "Examples:",
        "  pumpkinpi --help",
        "  pumpkinpi server --host 127.0.0.1 --port 9001",
        "",
        "Run `pumpkinpi <subcommand> --help` for command-specific options.",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)

    if not args or args[0] in {"-h", "--help", "help"}:
        print(_build_help())
        return 0

    subcommand = args[0]
    scripts = _discover_scripts()
    script_path = scripts.get(subcommand)
    if script_path is None:
        print(f"Unknown subcommand: '{subcommand}'", file=sys.stderr)
        print(file=sys.stderr)
        print(_build_help(), file=sys.stderr)
        return 2

    return subprocess.run(
        [sys.executable, str(script_path), *args[1:]],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
