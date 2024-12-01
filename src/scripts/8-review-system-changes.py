import os
import subprocess
import time
from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

# Set up directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

console = Console()

def generate_report_filename(scan_type):
    """Generate timestamped JSON filename."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{scan_type}_Report_{timestamp}.json"

def save_json(data, scan_type):
    """Save data as JSON file."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as f:
        json.dump(data, f, indent=4)
    return report_file

def explain_process():
    """Display purpose using styled panel."""
    console.print(Panel(
        "[bold magenta]Major System Changes Check[/bold magenta]\n"
        "- Scans for installations, updates, deleted, or moved files in the last 7 days.\n"
        "- Results are saved as detailed JSON files.", border_style="magenta"))

def check_logs(predicate, description):
    """Fetch log entries matching the predicate."""
    result = subprocess.run(
        ["log", "show", "--predicate", predicate, "--info", "--last", "7d"],
        capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if description in line]

def process_scan():
    """Perform system scans and structure results."""
    start_time = time.time()

    # Metadata
    metadata = {
        "scan_name": "Major System Changes",
        "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tool_name": "System Logs Analyzer",
        "scan_duration": None
    }

    # Scan results
    results = {
        "installations_updates": check_logs(
            'eventMessage CONTAINS[c] "installed" OR eventMessage CONTAINS[c] "updated"', 
            "Installed"
        ),
        "deleted_moved_files": check_logs(
            'eventMessage CONTAINS[c] "deleted" OR eventMessage CONTAINS[c] "moved"',
            "deleted"
        )
    }

    # Summary
    summary = {
        "total_installations_updates": len(results["installations_updates"]),
        "total_deleted_moved_files": len(results["deleted_moved_files"]),
        "overall_status": "Issues Detected" if any(results.values()) else "No Significant Changes"
    }

    metadata["scan_duration"] = f"{time.time() - start_time:.2f} seconds"

    # Combine data
    report_data = {
        "scan_metadata": metadata,
        "results": results,
        "summary": summary
    }

    return report_data

def main():
    explain_process()

    # Progress tracker
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("Scanning system...", total=2)

        # Perform scan and save results
        report_data = process_scan()
        progress.update(task, advance=2)

        # Save as JSON
        report_file = save_json(report_data, "Major_System_Changes")
        console.print(f"\n[bold green]Scan completed. Report saved at:[/bold green] [bold magenta]{report_file}[/bold magenta]")

if __name__ == "__main__":
    main()