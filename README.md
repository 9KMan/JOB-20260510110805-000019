# Human Data Manager — Annotation Pipeline System

Production-ready project — see SPEC.md for full documentation.

## Architecture
Annotation Pipeline System for AI training data workflows:
- [CSV/JSON Import] → [UPLOAD] → [ANNOTATE] → [REVIEW] → [APPROVED]
- KPI Dashboard: throughput/hr, approval rate, cycle time per stage
- Weekly automated report generation via cron

## Data Sources
| Source | Type | Fields |
|--------|------|--------|
| CSV import | File | item_id, raw_data, priority |
| JSON import | File | item_id, raw_data, priority |
| Manual entry | CLI | via advance command |

## Data Model
SQLite schema (items, annotators, events tables):
- **items**: id, raw_data, stage, annotator_id, priority, created_at, stage_entered_at, rejection_note
- **annotators**: id, items_completed, items_rejected, avg_cycle_time_hrs
- **events**: id, item_id, event_type, from_stage, to_stage, timestamp

## CLI Reference
```bash
python main.py import --file data.csv --annotator alice --priority high
python main.py advance --item-id ITEM-001 --stage ANNOTATE --annotator alice
python main.py reject --item-id ITEM-001 --note "Missing label"
python main.py list --stage ANNOTATE
python main.py dashboard
python main.py dashboard --annotator alice
python main.py report --period weekly
```

## Installation
```bash
pip install -r requirements.txt
python main.py --help
```

## Quality Guarantees
- All stage transitions logged to events table (full audit trail)
- Rejection tracking with notes (annotator accountability)
- Cycle time measurement accurate to ± 1 minute
- Import validation: valid rows continue, invalid rows logged but skipped

## Output Format
- Dashboard: tabular text output (default) or JSON (--format json)
- Weekly report: JSON file at reports/YYYY-WXX.json + CSV breakdown
- All timestamps in UTC ISO 8601 format

## Project Structure
```
.
├── main.py           # CLI entry point (Click)
├── db.py             # SQLite schema + connection
├── models.py         # items, annotators, events data classes
├── commands/
│   ├── import_cmd.py # bulk import from CSV/JSON
│   ├── advance_cmd.py # stage advancement
│   ├── reject_cmd.py  # rejection with notes
│   ├── list_cmd.py    # list items by stage
│   ├── dashboard_cmd.py # KPI output
│   └── report_cmd.py  # weekly report generation
├── schema.sql        # SQLite DDL
├── requirements.txt  # click, jinja2
└── README.md
```

## Limitations
- Single-user CLI tool (no multi-annotator authentication)
- No real-time web dashboard (static output only)
- No ML model integration (human-in-the-loop only)
- SQLite backend (not suitable for multi-node deployment)
