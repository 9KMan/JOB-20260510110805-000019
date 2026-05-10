# Human Data Manager — Annotation Pipeline System

## 1. Project Overview

**Client:** micro1 AI
**Goal:** Build an internal annotation workflow management system for AI training data pipelines
**Core Function:** Track data items through annotation stages, measure annotator throughput, surface quality KPIs, and generate weekly operational reports

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Annotation Pipeline                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [CSV/JSON Import]                                       │
│         │                                                │
│         ▼                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   UPLOAD    │───▶│  ANNOTATE   │───▶│   REVIEW    │  │
│  │   Stage     │    │   Stage     │    │   Stage     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                 │                 │          │
│         ▼                 ▼                 ▼          │
│  ┌──────────────────────────────────────────────┐      │
│  │              Metrics Dashboard                │      │
│  │  • Items per stage  • Throughput/hr         │      │
│  │  • Annotator output  • Quality scores         │      │
│  └──────────────────────────────────────────────┘      │
│         │                                                │
│         ▼                                                │
│  ┌─────────────┐    ┌─────────────┐                      │
│  │   APPROVED  │    │   EXPORT    │                      │
│  └─────────────┘    └─────────────┘                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. Upload raw data items (CSV/JSON via CLI)
2. Assign items to annotators → moves to ANNOTATE stage
3. Annotator submits → moves to REVIEW stage
4. Reviewer approves/rejects → APPROVED or back to ANNOTATE
5. Weekly automated report generation via cron

## 3. Core Workstreams

### Workstream 1 — Data Import
- CLI command: `python main.py import --file data.csv --annotator alice --priority high`
- Supported formats: CSV, JSON (array of objects)
- Auto-generate unique item IDs
- Stage: UPLOAD (initial state)
- Store: `items` table with status, annotator, priority, timestamps

### Workstream 2 — Annotation Stage Management
- Move items through stages: UPLOAD → ANNOTATE → REVIEW → APPROVED
- CLI: `python main.py advance --item-id ITEM-001 --stage ANNOTATE --annotator alice`
- Track per-item: annotator_id, stage_entered_at, stage_exited_at
- Rejection: item returns to ANNOTATE with rejection note

### Workstream 3 — KPI Dashboard
- **Throughput KPI:** items completed per annotator per day
- **Quality KPI:** approval rate (approved / submitted)
- **Cycle Time KPI:** average time in each stage
- **Volume KPI:** total items in pipeline, items per stage
- CLI: `python main.py dashboard` → prints tabular metrics
- JSON export: `python main.py dashboard --format json`

### Workstream 4 — Weekly Report Generation
- Cron job: `python main.py report --period weekly`
- Outputs: text summary + CSV breakdown by annotator
- Metrics: total items processed, approval rate, avg cycle time, top annotator
- Saves report to `reports/YYYY-WXX.json`

## 4. Data Model

### items table
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PRIMARY KEY | ITEM-XXX format |
| raw_data | TEXT | JSON string of original item |
| stage | TEXT | UPLOAD / ANNOTATE / REVIEW / APPROVED / REJECTED |
| annotator_id | TEXT | Current or last annotator |
| priority | TEXT | high / medium / low |
| created_at | TIMESTAMP | Import time |
| stage_entered_at | TIMESTAMP | When current stage started |
| rejection_note | TEXT | NULL unless rejected once |

### annotators table
| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PRIMARY KEY | annotator name |
| items_completed | INTEGER | Total approved items |
| items_rejected | INTEGER | Total rejections |
| avg_cycle_time_hrs | REAL | Rolling average |

### events table
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PRIMARY KEY | Auto-increment |
| item_id | TEXT | FK to items |
| event_type | TEXT | stage_change / rejection / approval |
| from_stage | TEXT | NULL for import |
| to_stage | TEXT | NULL for final |
| timestamp | TIMESTAMP | Event time |

## 5. API Design

No REST API — CLI-only tool for security isolation:

| Command | Purpose |
|---------|---------|
| `python main.py import --file <path> --annotator <name>` | Bulk import items |
| `python main.py advance --item-id <id> --stage <name> --annotator <name>` | Move item to next stage |
| `python main.py reject --item-id <id> --note <text>` | Reject and return to ANNOTATE |
| `python main.py dashboard` | Print current KPI summary |
| `python main.py dashboard --annotator <name>` | Filter KPIs to one annotator |
| `python main.py report --period weekly` | Generate weekly report |
| `python main.py list --stage <name>` | List items in a stage |

## 6. Technical Decisions

1. **SQLite for storage** — single file, zero setup, portable. Appropriate for single-user internal tool at MICRO scope.
2. **CLI-only (no web server)** — security isolation, no authentication surface, runs on local machine
3. **JSON for raw data storage** — flexibility for heterogeneous input formats without schema migrations
4. **Cron-driven reports** — `report --period weekly` called by external scheduler, outputs timestamped JSON files
5. **No external dependencies beyond stdlib + sqlite3** — keeps the tool portable and installable via `pip install -e .`

## 7. Out of Scope

- User authentication / annotator accounts
- Real-time web dashboard (static dashboard output only)
- Machine learning model integration
- Multi-workspace support
- Data versioning / git-like history

## 8. Success Metrics

- Import 1000 items via CSV in < 5 seconds
- Dashboard loads in < 1 second for 10K items
- Weekly report generates in < 3 seconds
- All items traceable from UPLOAD → APPROVED with full event history
- Cycle time measurement accurate to ± 1 minute