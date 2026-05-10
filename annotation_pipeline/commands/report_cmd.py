"""Weekly report generation."""
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from annotation_pipeline.db import get_connection


def get_week_range(period: str = "weekly") -> tuple[datetime, datetime]:
    now = datetime.now()
    if period == "weekly":
        start = now - timedelta(days=7)
    else:
        start = now - timedelta(days=30)
    return start, now


def generate_report(period: str = "weekly", output_dir: str = "reports") -> dict:
    start_dt, end_dt = get_week_range(period)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    conn.row_factory = lambda c, r: {d[0]: r[i] for i, d in enumerate(c.description)}
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as cnt FROM events
        WHERE event_type = 'stage_change'
        AND timestamp >= ?
        AND timestamp <= ?
    """, (start_dt.isoformat(), end_dt.isoformat()))
    total_processed = cursor.fetchone()["cnt"] if cursor.fetchone() else 0

    cursor.execute("""
        SELECT annotator_id, COUNT(*) as cnt FROM events
        WHERE event_type = 'stage_change'
        AND timestamp >= ?
        AND timestamp <= ?
        GROUP BY annotator_id
    """, (start_dt.isoformat(), end_dt.isoformat()))
    by_annotator_raw = cursor.fetchall()

    annotator_stats = defaultdict(lambda: {"processed": 0, "approved": 0, "rejected": 0})

    for row in by_annotator_raw:
        annotator_stats[row["annotator_id"]]["processed"] = row["cnt"]

    cursor.execute("""
        SELECT annotator_id, COUNT(*) as cnt FROM events
        WHERE event_type = 'stage_change' AND to_stage = 'APPROVED'
        AND timestamp >= ?
        AND timestamp <= ?
        GROUP BY annotator_id
    """, (start_dt.isoformat(), end_dt.isoformat()))
    for row in cursor.fetchall():
        annotator_stats[row["annotator_id"]]["approved"] = row["cnt"]

    cursor.execute("""
        SELECT annotator_id, COUNT(*) as cnt FROM events
        WHERE event_type = 'rejection'
        AND timestamp >= ?
        AND timestamp <= ?
        GROUP BY annotator_id
    """, (start_dt.isoformat(), end_dt.isoformat()))
    for row in cursor.fetchall():
        annotator_stats[row["annotator_id"]]["rejected"] = row["cnt"]

    total_approved = sum(s["approved"] for s in annotator_stats.values())
    total_rejected = sum(s["rejected"] for s in annotator_stats.values())
    approval_rate = (total_approved / total_processed * 100) if total_processed > 0 else 0

    top_annotator = max(annotator_stats.items(), key=lambda x: x[1]["processed"], default=(None, {}))
    top_name = top_annotator[0] if top_annotator[0] else "N/A"
    top_count = top_annotator[1]["processed"] if top_annotator[1] else 0

    report = {
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "range_start": start_dt.isoformat(),
        "range_end": end_dt.isoformat(),
        "total_items_processed": total_processed,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "approval_rate": approval_rate,
        "top_annotator": {"name": top_name, "items": top_count},
        "by_annotator": {k: dict(v) for k, v in annotator_stats.items()},
    }

    week_num = int(end_dt.strftime("%W"))
    report_filename = f"{end_dt.year}-W{week_num:02d}.json"
    report_path = output_path / report_filename

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    csv_filename = f"{end_dt.year}-W{week_num:02d}_by_annotator.csv"
    csv_path = output_path / csv_filename
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["annotator_id", "processed", "approved", "rejected", "approval_rate"])
        for annotator, stats in annotator_stats.items():
            rate = (stats["approved"] / stats["processed"] * 100) if stats["processed"] > 0 else 0
            writer.writerow([annotator, stats["processed"], stats["approved"], stats["rejected"], f"{rate:.1f}%"])

    conn.close()

    summary = f"""
{'='*50}
        WEEKLY OPERATIONAL REPORT
{'='*50}
Period: {start_dt.date()} to {end_dt.date()}
Generated: {datetime.now().date()}

Total Items Processed: {total_processed}
Total Approved: {total_approved}
Total Rejected: {total_rejected}
Approval Rate: {approval_rate:.1f}%

Top Annotator: {top_name} ({top_count} items)

Reports saved:
  - {report_path}
  - {csv_path}
{'='*50}
"""
    print(summary.strip())
    return report


def main(args):
    try:
        period = args.get("period", "weekly")
        output_dir = args.get("output", "reports")
        generate_report(period, output_dir)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
