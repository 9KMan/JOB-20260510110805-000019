"""Annotation Pipeline CLI."""
import argparse
import sys

from annotation_pipeline.db import init_db
from annotation_pipeline.commands import (
    advance_main,
    dashboard_main,
    import_main,
    list_main,
    reject_main,
    report_main,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Annotation Pipeline CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    import_parser = subparsers.add_parser("import", help="Import items from CSV/JSON")
    import_parser.add_argument("--file", required=True, help="Path to CSV or JSON file")
    import_parser.add_argument("--annotator", required=True, help="Annotator name")
    import_parser.add_argument("--priority", default="medium", help="Priority: high/medium/low")

    advance_parser = subparsers.add_parser("advance", help="Move item to next stage")
    advance_parser.add_argument("--item-id", required=True, help="Item ID")
    advance_parser.add_argument("--stage", required=True, help="Target stage")
    advance_parser.add_argument("--annotator", required=True, help="Annotator name")

    reject_parser = subparsers.add_parser("reject", help="Reject an item")
    reject_parser.add_argument("--item-id", required=True, help="Item ID")
    reject_parser.add_argument("--note", default="", help="Rejection note")

    list_parser = subparsers.add_parser("list", help="List items")
    list_parser.add_argument("--stage", help="Filter by stage")
    list_parser.add_argument("--annotator", help="Filter by annotator")

    dashboard_parser = subparsers.add_parser("dashboard", help="Show KPI dashboard")
    dashboard_parser.add_argument("--annotator", help="Filter by annotator")
    dashboard_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--period", choices=["weekly", "monthly"], default="weekly", help="Report period")
    report_parser.add_argument("--output", default="reports", help="Output directory")

    return parser


def main():
    init_db()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    command_map = {
        "import": import_main,
        "advance": advance_main,
        "reject": reject_main,
        "list": list_main,
        "dashboard": dashboard_main,
        "report": report_main,
    }

    cmd = vars(args)
    command_map[args.command](cmd)


if __name__ == "__main__":
    main()
