"""CLI entry point for silicon-eye."""

from __future__ import annotations

import argparse
import logging
import sys

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
    try:
        pipeline = Pipeline(config, data_root=args.data_root, output_dir=args.output)
        results = pipeline.run(stages=args.stages, registration_spec=args.registration_spec)
    except (ValueError, OSError) as error:
        raise SystemExit(f"Pipeline failed: {error}") from error
    print(f"Pipeline stage report for '{config.chip.name}': {pipeline.run_dir}")
    for phase, info in results.items():
        print(f"  {phase}: {info}")
    if any(info["status"] in {"blocked", "failed"} for info in results.values()):
        raise SystemExit(2)


def cmd_annotate(args: argparse.Namespace) -> None:
    """Annotation subcommands."""
    if args.subcommand == "parse":
        from .annotation_parser import parse_command

        parse_command(args.input, args.output, args.pixel_per_um)
    elif args.subcommand == "materials":
        from .material_review import run_material_review

        try:
            result = run_material_review(args.spec, args.output)
        except (ValueError, OSError) as error:
            raise SystemExit(f"Material review export failed: {error}") from error
        print(f"AA/poly/CT candidate review: {args.output}; {result['layers']}")
    elif args.subcommand == "guided":
        from .guided_materials import run_guided

        try:
            result = run_guided(args.spec, args.output)
        except (ValueError, OSError) as error:
            raise SystemExit(f"Guided material extraction failed: {error}") from error
        print(f"Guided candidate evidence: {args.output}; status={result['material_status']}")
        print("Positive examples used for fitting; no independent accuracy claim.")
    elif args.subcommand == "contours":
        from .material_contours import run_contours

        try:
            result = run_contours(args.spec, args.output)
        except (ValueError, OSError) as error:
            raise SystemExit(f"Candidate contour generation failed: {error}") from error
        print(f"Candidate contour evidence: {args.output}; {len(result['objects'])} ROIs")
        print("Material identity unknown; units=px; no device truth generated.")
    elif args.subcommand == "review":
        from .pixel_annotations import review_annotations

        try:
            result = review_annotations(args.input, args.output)
        except (ValueError, OSError) as error:
            raise SystemExit(f"Pixel annotation review failed: {error}") from error
        print(f"Pixel annotation evidence: {args.output}; {result['object_count']} objects")
        print(
            f"Geometry states: {result['geometry_status_counts']}; "
            f"device_ground_truth_ready={result['device_ground_truth_ready']}"
        )
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
            print(
                f"Annotations: {len(config.annotations.device_hints)} device hints, "
                f"{len(config.annotations.regions)} regions"
            )


def cmd_register(args: argparse.Namespace) -> None:
    """Build a registration evidence pack with independent point evaluation."""
    from .registration_audit import run_audit

    try:
        manifest = run_audit(
            args.config,
            args.data_root,
            args.reference,
            args.output,
            args.fit_roi,
            args.points,
            args.method,
            args.transform_type,
            args.max_dimension,
            args.threshold_px,
            args.constraints,
        )
    except (ValueError, OSError) as error:
        raise SystemExit(f"Registration audit failed: {error}") from error
    print(f"Evidence pack: {args.output}; {len(manifest['layers'])} layers recorded")
    print("See report.md for solver and independent evaluation status.")


def cmd_register_local(args: argparse.Namespace) -> None:
    """Run one local candidate case, including optional frozen model checks."""
    from .registration_local import run_local

    try:
        result = run_local(args.spec, args.output)
    except (ValueError, OSError) as error:
        raise SystemExit(f"Local registration audit failed: {error}") from error
    metrics = result["validation_metrics"]
    print(f"Evidence pack: {args.output}")
    print(
        f"P95={metrics['p95_px']:.2f}px; max={metrics['max_px']:.2f}px; "
        f"numeric_budget_met={result['numeric_budget_met']}; acceptance={result['acceptance']}"
    )
    print("See report.md for local scope and candidate correspondence evidence.")


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
        choices=["registration", "phase1", "phase2"],
        help="Pipeline stages to run (default: phase1 phase2)",
    )
    run_parser.add_argument("--data-root", default="data")
    run_parser.add_argument("-o", "--output", help="New run directory; existing paths refused")
    run_parser.add_argument("--registration-spec", help="Local candidate registration case JSON")
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
    review_parser = ann_sub.add_parser("review", help="Validate/render source-pixel ROI drafts")
    review_parser.add_argument("-i", "--input", required=True)
    review_parser.add_argument(
        "-o", "--output", required=True, help="New evidence directory; source images are protected"
    )
    contour_parser = ann_sub.add_parser("contours", help="Build local material boundary hypotheses")
    contour_parser.add_argument("--spec", required=True)
    contour_parser.add_argument("-o", "--output", required=True)
    guided_parser = ann_sub.add_parser(
        "guided", help="Refine human material examples on raw images"
    )
    guided_parser.add_argument("--spec", required=True)
    guided_parser.add_argument("-o", "--output", required=True)
    materials_parser = ann_sub.add_parser("materials", help="Export AA/poly/CT in review order")
    materials_parser.add_argument("--spec", required=True)
    materials_parser.add_argument("-o", "--output", required=True)
    ann_parser.set_defaults(func=cmd_annotate)

    # ── info ──
    info_parser = subparsers.add_parser("info", help="Show config/checkpoint info")
    info_parser.add_argument("-c", "--config", help="Path to chip config YAML")
    info_parser.set_defaults(func=cmd_info)

    register_parser = subparsers.add_parser("register", help="Audit cross-layer registration")
    register_parser.add_argument("-c", "--config", required=True)
    register_parser.add_argument("--data-root", default="data")
    register_parser.add_argument("--reference", required=True)
    register_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="New evidence directory; existing directories are refused",
    )
    register_parser.add_argument(
        "--fit-roi", type=int, nargs=4, required=True, metavar=("X", "Y", "WIDTH", "HEIGHT")
    )
    register_parser.add_argument("--points", help="Independent source-hash-bound point JSON")
    register_parser.add_argument(
        "--constraints", help="Separate structural fit anchors and locked budget"
    )
    register_parser.add_argument("--method", choices=["orb", "ecc", "auto"], default="orb")
    register_parser.add_argument(
        "--transform-type", choices=["similarity", "affine", "homography"], default="similarity"
    )
    register_parser.add_argument("--max-dimension", type=int, default=1600)
    register_parser.add_argument(
        "--threshold-px",
        type=float,
        help="Error budget fixed before fitting; omitted means unknown",
    )
    register_parser.set_defaults(func=cmd_register)

    local_parser = subparsers.add_parser("register-local", help="Audit a small local case")
    local_parser.add_argument("--spec", required=True, help="Local case input JSON")
    local_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="New evidence directory; existing directories are refused",
    )
    local_parser.set_defaults(func=cmd_register_local)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
