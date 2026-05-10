"""Advance items through stages."""
import sys

from annotation_pipeline.db import get_connection
from annotation_pipeline.models import VALID_STAGES


def advance_item(item_id: str, stage: str, annotator: str) -> None:
    stage = stage.upper()
    if stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: {stage}. Must be one of {VALID_STAGES}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, stage FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise ValueError(f"Item not found: {item_id}")

    current_stage = item["stage"]

    cursor.execute(
        """
        UPDATE items
        SET stage = ?, annotator_id = ?, stage_entered_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (stage, annotator, item_id),
    )

    cursor.execute(
        """
        INSERT INTO events (item_id, event_type, from_stage, to_stage)
        VALUES (?, 'stage_change', ?, ?)
        """,
        (item_id, current_stage, stage),
    )

    conn.commit()
    conn.close()
    print(f"Moved {item_id}: {current_stage} → {stage}")


def main(args):
    try:
        advance_item(args["item_id"], args["stage"], args["annotator"])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
