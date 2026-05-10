"""CLI commands package."""
from annotation_pipeline.commands.advance_cmd import main as advance_main
from annotation_pipeline.commands.dashboard_cmd import main as dashboard_main
from annotation_pipeline.commands.import_cmd import main as import_main
from annotation_pipeline.commands.list_cmd import main as list_main
from annotation_pipeline.commands.reject_cmd import main as reject_main
from annotation_pipeline.commands.report_cmd import main as report_main

__all__ = [
    "advance_main",
    "dashboard_main",
    "import_main",
    "list_main",
    "reject_main",
    "report_main",
]
