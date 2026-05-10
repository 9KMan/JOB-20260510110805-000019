"""Reject an item and return it to ANNOTATE stage."""
import sys

from annotation_pipeline.db import get_connection


def reject_item(item_id: str, note: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, stage FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise ValueError(f"Item not found: {item_id}")

    current_stage = item["stage"]

    if current_stage == "APPROVED":
        conn.close()
        raise ValueError(f"Cannot reject already approved item: {item_id}")

    cursor.execute(
        """
        UPDATE items
        SET stage = 'ANNOTATE', rejection_note = ?, stage_entered_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (note, item_id),
    )

    cursor.execute(
        """
        INSERT INTO events (item_id, event_type, from_stage, to_stage)
        VALUES (?, 'rejection', ?, 'ANNOTATE')
        """,
        (item_id, current_stage),
    )

    conn.commit()
    conn.close()
    print(f"Rejected {item_id}: {current_stage} → ANNOTATE (note: {note})")


def main(args):
    try:
        reject_item(args["item_id"], args.get("note", ""))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
