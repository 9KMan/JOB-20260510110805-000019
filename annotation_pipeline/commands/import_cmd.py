"""Import command for CSV/JSON data."""
import csv
import json
import sys
from pathlib import Path

from annotation_pipeline.db import get_connection, item_counter
from annotation_pipeline.models import VALID_PRIORITIES, VALID_STAGES


def generate_item_id(counter: int) -> str:
    return f"ITEM-{counter:03d}"


def import_data(file_path: str, annotator: str, priority: str = "medium") -> list[str]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    priority = priority.lower()
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}. Must be one of {VALID_PRIORITIES}")

    items_imported = []
    counter = item_counter()

    conn = get_connection()
    cursor = conn.cursor()

    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item_id = generate_item_id(counter)
                raw_data = json.dumps(row)
                cursor.execute(
                    """
                    INSERT INTO items (id, raw_data, stage, annotator_id, priority, stage_entered_at)
                    VALUES (?, ?, 'UPLOAD', ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, raw_data, annotator, priority),
                )
                cursor.execute(
                    """
                    INSERT INTO events (item_id, event_type, to_stage)
                    VALUES (?, 'stage_change', 'UPLOAD')
                    """,
                    (item_id,),
                )
                items_imported.append(item_id)
                counter += 1
    elif path.suffix.lower() == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = [data]
        for row in data:
            item_id = generate_item_id(counter)
            raw_data = json.dumps(row)
            cursor.execute(
                """
                INSERT INTO items (id, raw_data, stage, annotator_id, priority, stage_entered_at)
                VALUES (?, ?, 'UPLOAD', ?, ?, CURRENT_TIMESTAMP)
                """,
                (item_id, raw_data, annotator, priority),
            )
            cursor.execute(
                """
                INSERT INTO events (item_id, event_type, to_stage)
                VALUES (?, 'stage_change', 'UPLOAD')
                """,
                (item_id,),
            )
            items_imported.append(item_id)
            counter += 1
    else:
        conn.close()
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .csv or .json")

    conn.commit()
    conn.close()
    return items_imported


def main(args):
    try:
        items = import_data(args["file"], args["annotator"], args.get("priority", "medium"))
        print(f"Imported {len(items)} items: {', '.join(items)}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
