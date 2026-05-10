"""KPI Dashboard command."""
import json
import sys
from collections import defaultdict
from typing import Optional

from annotation_pipeline.db import get_connection


def calculate_kpis(annotator: Optional[str] = None) -> dict:
    conn = get_connection()
    conn.row_factory = lambda c, r: {d[0]: r[i] for i, d in enumerate(c.description)}
    cursor = conn.cursor()

    kpis = {
        "total_items": 0,
        "items_per_stage": defaultdict(int),
        "throughput_per_annotator": defaultdict(int),
        "approval_rate": 0.0,
        "rejection_count": 0,
        "avg_cycle_time_hrs": 0.0,
    }

    query = """
        SELECT stage, annotator_id,
               (julianday(CURRENT_TIMESTAMP) - julianday(stage_entered_at)) * 24 as hrs_in_stage
        FROM items WHERE 1=1
    """
    params = []
    if annotator:
        query += " AND annotator_id = ?"
        params.append(annotator)

    cursor.execute(query, params)
    items = cursor.fetchall()

    total_items = len(items)
    kpis["total_items"] = total_items

    for item in items:
        kpis["items_per_stage"][item["stage"]] += 1
        if item["annotator_id"]:
            kpis["throughput_per_annotator"][item["annotator_id"]] += 1

    cursor.execute("""
        SELECT COUNT(*) FROM events WHERE event_type = 'stage_change' AND to_stage = 'APPROVED'
    """)
    result = cursor.fetchone()
    approved_count = result["COUNT(*)"] if result else 0

    cursor.execute("""
        SELECT COUNT(*) FROM events WHERE event_type = 'rejection'
    """)
    result = cursor.fetchone()
    kpis["rejection_count"] = result["COUNT(*)"] if result else 0

    cursor.execute("""
        SELECT COUNT(*) FROM events WHERE event_type = 'stage_change' AND to_stage = 'REVIEW'
    """)
    result = cursor.fetchone()
    submitted_count = result["COUNT(*)"] if result else 0

    if submitted_count > 0:
        kpis["approval_rate"] = approved_count / submitted_count

    if total_items > 0:
        total_hrs = sum(item["hrs_in_stage"] for item in items if item["hrs_in_stage"])
        kpis["avg_cycle_time_hrs"] = total_hrs / total_items if total_items > 0 else 0

    kpis["items_per_stage"] = dict(kpis["items_per_stage"])
    kpis["throughput_per_annotator"] = dict(kpis["throughput_per_annotator"])

    conn.close()
    return kpis


def format_dashboard(kpis: dict) -> str:
    lines = [
        "=" * 50,
        "        ANNOTATION PIPELINE KPI DASHBOARD",
        "=" * 50,
        f"\nTotal Items in Pipeline: {kpis['total_items']}",
        "\nItems per Stage:",
    ]
    for stage, count in sorted(kpis["items_per_stage"].items()):
        lines.append(f"  {stage:<15}: {count}")

    lines.append("\nThroughput per Annotator (items completed):")
    for annotator, count in sorted(kpis["throughput_per_annotator"].items()):
        lines.append(f"  {annotator:<15}: {count}")

    approval_pct = kpis["approval_rate"] * 100
    lines.append(f"\nApproval Rate: {approval_pct:.1f}%")
    lines.append(f"Total Rejections: {kpis['rejection_count']}")
    lines.append(f"\nAvg Cycle Time: {kpis['avg_cycle_time_hrs']:.2f} hours")
    lines.append("=" * 50)
    return "\n".join(lines)


def main(args):
    try:
        annotator = args.get("annotator")
        kpis = calculate_kpis(annotator)

        if args.get("format") == "json":
            print(json.dumps(kpis, indent=2))
        else:
            print(format_dashboard(kpis))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
