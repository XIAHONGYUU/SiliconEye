"""CLI entry point for silicon-eye."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import load_config
from .pipeline import Pipeline


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_run(args: argparse.Namespace) -> None:
    """Run the reverse engineering pipeline."""
    config = load_config(args.config)
    pipeline = Pipeline(config)
    results = pipeline.run(stages=args.stages)

    print(f"\n✓ Pipeline complete for '{config.chip.name}'")
    for phase, info in results.items():
        print(f"  {phase}: {info}")


def cmd_annotate(args: argparse.Namespace) -> None:
    """Annotation subcommands."""
    if args.subcommand == "parse":
        from .annotation_parser import parse_command

        parse_command(args.input, args.output, args.pixel_per_um)
    else:
        print(f"Unknown annotate subcommand: {args.subcommand}")
        sys.exit(1)


def cmd_info(args: argparse.Namespace) -> None:
    """Show information about a config or checkpoint."""
    if args.config:
        config = load_config(args.config)
        print(f"Chip: {config.chip.name}")
        print(f"Process: {config.chip.process}")
        print(f"Layers: {len(config.layers)}")
        for layer in config.layers:
            print(f"  [{layer.index}] {layer.name}: {layer.description}")
        print(f"Tiles: {len(config.tiles)}")
        if config.annotations and not config.annotations.is_empty:
            print(f"Annotations: {len(config.annotations.device_hints)} device hints, "
                  f"{len(config.annotations.regions)} regions")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="silicon-eye",
        description="AI-assisted analog circuit reverse engineering",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── run ──
    run_parser = subparsers.add_parser("run", help="Run the pipeline")
    run_parser.add_argument("-c", "--config", required=True, help="Path to chip config YAML")
    run_parser.add_argument(
        "-s",
        "--stages",
        nargs="+",
        default=["phase1", "phase2"],
        choices=["phase1", "phase2"],
        help="Pipeline stages to run (default: phase1 phase2)",
    )
    run_parser.set_defaults(func=cmd_run)

    # ── annotate ──
    ann_parser = subparsers.add_parser("annotate", help="Annotation tools")
    ann_sub = ann_parser.add_subparsers(dest="subcommand")

    parse_parser = ann_sub.add_parser("parse", help="Parse color-block annotated image")
    parse_parser.add_argument("-i", "--input", required=True, help="Annotated image path")
    parse_parser.add_argument("-o", "--output", required=True, help="Output YAML config path")
    parse_parser.add_argument(
        "--pixel-per-um", type=float, default=20.0, help="Image scale (default: 20.0 px/μm)"
    )
    ann_parser.set_defaults(func=cmd_annotate)

    # ── info ──
    info_parser = subparsers.add_parser("info", help="Show config/checkpoint info")
    info_parser.add_argument("-c", "--config", help="Path to chip config YAML")
    info_parser.set_defaults(func=cmd_info)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
