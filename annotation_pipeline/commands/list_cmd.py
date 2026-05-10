"""List items by stage."""
import sys
from typing import Optional

from annotation_pipeline.db import get_connection
from annotation_pipeline.models import VALID_STAGES


def list_items(stage: Optional[str] = None, annotator: Optional[str] = None) -> list:
    conn = get_connection()
    conn.row_factory = lambda c, r: {d[0]: r[i] for i, d in enumerate(c.description)}
    cursor = conn.cursor()

    query = "SELECT id, stage, annotator_id, priority, created_at, stage_entered_at FROM items WHERE 1=1"
    params = []

    if stage:
        stage = stage.upper()
        if stage not in VALID_STAGES:
            conn.close()
            raise ValueError(f"Invalid stage: {stage}. Must be one of {VALID_STAGES}")
        query += " AND stage = ?"
        params.append(stage)

    if annotator:
        query += " AND annotator_id = ?"
        params.append(annotator)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    items = cursor.fetchall()
    conn.close()
    return items


def main(args):
    try:
        stage = args.get("stage")
        annotator = args.get("annotator")
        items = list_items(stage, annotator)

        if not items:
            print("No items found.")
            return

        print(f"{'ID':<12} {'STAGE':<10} {'ANNOTATOR':<15} {'PRIORITY':<10} {'CREATED AT'}")
        print("-" * 70)
        for item in items:
            print(
                f"{item['id']:<12} {item['stage']:<10} {item['annotator_id'] or 'N/A':<15} "
                f"{item['priority']:<10} {item['created_at']}"
            )
        print(f"\nTotal: {len(items)} items")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
