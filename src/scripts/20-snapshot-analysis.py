#!/usr/bin/env python3

import os
import subprocess
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Define directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_report_filename(scan_type):
    """Generate a timestamped JSON filename."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{scan_type}_Report_{timestamp}.json"

def save_json(data, scan_type):
    """Save data to a JSON file."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as f:
        json.dump(data, f, indent=4)
    return report_file

console = Console()

class SnapshotAnalyzer:
    def __init__(self):
        self.results = {
            "snapshots": [],
            "total_snapshots": 0,
            "recent_snapshots": 0,
            "errors": None
        }

    def explain_process(self):
        """Explain the process of snapshot analysis."""
        console.print(Panel(
            "[cyan]Performing Snapshot Analysis[/cyan]\n"
            "This script will check for available Time Machine snapshots.\n"
            "It will perform the following checks:\n"
            " - List of all available snapshots\n"
            " - Highlight recent snapshots (within the last 7 days)\n"
            " - Provide details on each snapshot (creation date, age)\n"
            "\nRegular snapshots can help restore system state in case of issues.\n",
            title="Snapshot Analysis",
            border_style="cyan"
        ))

    def analyze_snapshots(self):
        """Analyze available Time Machine snapshots."""
        console.print("\n[bold]Step 1: Listing Available Snapshots[/bold]")

        try:
            # Run tmutil command to list local snapshots
            result = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True).stdout
            snapshots = [line for line in result.splitlines() if line.startswith("com.apple.TimeMachine")]
            self.results["total_snapshots"] = len(snapshots)

            if snapshots:
                table = Table(title="Available Snapshots", show_header=True, header_style="bold cyan")
                table.add_column("Snapshot", style="yellow")
                table.add_column("Created Date", style="green")
                table.add_column("Age (days)", justify="right", style="magenta")

                current_time = datetime.now()
                recent_count = 0

                for snapshot in snapshots:
                    snapshot_date_str = snapshot.split('.')[-1]
                    snapshot_date = datetime.strptime(snapshot_date_str, "%Y-%m-%d-%H%M%S")
                    age_days = (current_time - snapshot_date).days

                    snapshot_details = {
                        "snapshot": snapshot,
                        "created_date": snapshot_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "age_days": age_days,
                        "is_recent": age_days <= 7
                    }

                    if snapshot_details["is_recent"]:
                        recent_count += 1
                        console.print(f"[yellow]Recent snapshot: {snapshot} (Created: {snapshot_date}, Age: {age_days} days)[/yellow]")
                    else:
                        console.print(f"[green]Snapshot: {snapshot} (Created: {snapshot_date}, Age: {age_days} days)[/green]")

                    # Add snapshot details to the results and table
                    self.results["snapshots"].append(snapshot_details)
                    table.add_row(snapshot, snapshot_date.strftime("%Y-%m-%d %H:%M:%S"), str(age_days))

                console.print(table)
                self.results["recent_snapshots"] = recent_count
            else:
                console.print("[red]No Time Machine snapshots available on this system.[/red]")
                self.results["errors"] = "No Time Machine snapshots found."
        except Exception as e:
            error_message = f"Error analyzing snapshots: {str(e)}"
            console.print(f"[red]{error_message}[/red]")
            self.results["errors"] = error_message

        console.print("\n[cyan]Snapshot Analysis - Completed[/cyan]\n")

    def summarize_results(self):
        """Summarize the results of the snapshot analysis."""
        console.print("\n[bold cyan]═══ Summary of Snapshot Analysis ═══[/bold cyan]")

        # Save results to JSON
        report_file = save_json(self.results, "Snapshot_Analysis")
        console.print(f"[green]Snapshot analysis report saved to:[/green] [cyan]{report_file}[/cyan]")

    def perform_analysis(self):
        """Perform the snapshot analysis."""
        self.explain_process()

        # Step 1: Analyze snapshots
        self.analyze_snapshots()

        # Summarize results
        self.summarize_results()

def main():
    analyzer = SnapshotAnalyzer()
    analyzer.perform_analysis()

if __name__ == "__main__":
    main()