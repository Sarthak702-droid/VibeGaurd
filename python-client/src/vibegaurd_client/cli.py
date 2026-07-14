"""The `VIBEGAURD` Python console entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .client import BackendNotFoundError, CommandError, VibeGaurdClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIBEGAURD",
        description="Python client for the Rust-native VibeGuard backend.",
    )
    parser.add_argument("--backend", help="Path to the Rust vibeguard backend.")
    parser.add_argument("--timeout", type=float, default=60, help="Backend timeout in seconds.")
    commands = parser.add_subparsers(dest="command", required=True)

    scan_local = commands.add_parser("scan-local", help="Scan a locally pulled repository.")
    scan_local.add_argument("repository", type=Path)
    scan_local.add_argument("--format", default="json", choices=("json", "markdown", "sarif", "terminal"))
    scan_local.add_argument("--refresh", action="store_true")

    scan_github = commands.add_parser("scan-github", help="Scan a public GitHub HTTPS repository.")
    scan_github.add_argument("repository_url")
    scan_github.add_argument("--ref")
    scan_github.add_argument("--format", default="json", choices=("json", "markdown", "sarif", "terminal"))
    scan_github.add_argument("--refresh", action="store_true")

    passthrough = commands.add_parser("backend", help="Pass a reviewed argument sequence to Rust backend.")
    passthrough.add_argument("arguments", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = VibeGaurdClient(args.backend, timeout=args.timeout)
        if args.command == "scan-local":
            result = client.scan_local(args.repository, output_format=args.format, refresh=args.refresh)
        elif args.command == "scan-github":
            result = client.scan_public_github(
                args.repository_url,
                reference=args.ref,
                output_format=args.format,
                refresh=args.refresh,
            )
        else:
            if not args.arguments:
                raise ValueError("backend requires arguments after `--`, for example: backend -- doctor")
            result = client.run(args.arguments)
    except (BackendNotFoundError, CommandError, ValueError, OSError) as error:
        print(f"VIBEGAURD: {error}", file=sys.stderr)
        return getattr(error, "result", None).returncode if isinstance(error, CommandError) else 2
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
