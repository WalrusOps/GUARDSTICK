import os
import subprocess
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

# Define base and report directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))  # Root directory
SRC_DIR = os.path.join(ROOT_DIR, "src")                                        # Source directory
DATA_DIR = os.path.join(SRC_DIR, "data")                                       # Data directory
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")                            # Log reports directory
os.makedirs(REPORTS_DIR, exist_ok=True)

# Define a human-readable report filename with a timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_filename = f"Unsigned_Apps_Report_{timestamp}.json"
JSON_LOG_FILE = os.path.join(REPORTS_DIR, report_filename)

# Initialize data structure for JSON report
report_data = {
    "unsigned_apps": [],
    "signed_apps": [],
    "summary": []
}

# Initialize rich console
console = Console()

def log_to_json(section, data):
    """Log messages to the JSON report data structure."""
    report_data[section].append(data)

def explain_process():
    """Explain the purpose of the script with a styled panel."""
    panel_content = (
        "[bold magenta]🔍 Scanning for Unsigned macOS Applications 🔍[/bold magenta]\n\n"
        "This scan identifies applications that may not be verified by Apple.\n"
        "Unsigned apps could indicate potential security risks.\n\n"
        "All results will be logged for review."
    )
    console.print(Panel.fit(panel_content, border_style="magenta"))
    log_to_json("summary", {"description": panel_content})

def scan_for_unsigned_apps():
    """Scan for unsigned applications and log results."""
    console.print("[bold cyan]Step 1: Scanning for Unsigned Apps[/bold cyan]\n")
    log_to_json("summary", {"step": "Scanning for Unsigned Apps"})

    # Directories to scan for unsigned apps
    app_dirs = [
        "/Applications",
        os.path.expanduser("~/Applications")
    ]

    app_table = Table(title="Application Scan Results", show_header=True, header_style="bold blue")
    app_table.add_column("Application", style="green", width=40)
    app_table.add_column("Status", style="cyan", justify="center")

    for dir in app_dirs:
        if os.path.isdir(dir):
            console.print(f"[bold yellow]Checking {dir}...[/bold yellow]")
            log_to_json("summary", {"directory": dir, "status": "Checking"})

            # Check each app in the directory
            for app in track(os.listdir(dir), description="Scanning applications..."):
                app_path = os.path.join(dir, app)
                if os.path.isdir(app_path) and app.endswith(".app"):
                    result = subprocess.run(
                        ["spctl", "--assess", "--type", "exec", app_path],
                        capture_output=True, text=True
                    )

                    app_entry = {
                        "application_name": app,
                        "application_path": app_path,
                        "status": ""
                    }

                    # Log based on whether the app is signed or unsigned
                    if "rejected" in result.stderr:
                        app_entry["status"] = "unsigned"
                        app_table.add_row(app, "[red]⚠️ Unsigned[/red]")
                        log_to_json("unsigned_apps", app_entry)
                    else:
                        app_entry["status"] = "signed"
                        app_table.add_row(app, "[green]✅ Signed[/green]")
                        log_to_json("signed_apps", app_entry)
        else:
            console.print(f"[red]Directory {dir} does not exist.[/red]")
            log_to_json("summary", {"directory": dir, "status": "Directory does not exist"})
    
    console.print(app_table)

def summarize_results():
    """Summarize and log the scan results."""
    console.print("[bold cyan]Step 2: Summary of Unsigned Apps[/bold cyan]\n")
    log_to_json("summary", {"step": "Summary of Unsigned Apps"})

    # Count the number of signed and unsigned apps
    unsigned_count = len(report_data["unsigned_apps"])
    signed_count = len(report_data["signed_apps"])

    summary_table = Table(title="Scan Summary", show_header=True, header_style="bold blue")
    summary_table.add_column("Status", style="cyan", justify="left")
    summary_table.add_column("Count", style="bold green", justify="right")
    summary_table.add_row("Unsigned Apps", f"[red]{unsigned_count}[/red]")
    summary_table.add_row("Signed Apps", f"[green]{signed_count}[/green]")

    console.print(summary_table)

    # Append summary to the JSON report
    report_data["summary"].append({"unsigned_count": unsigned_count, "signed_count": signed_count})

def save_json_report():
    """Save the report data to a JSON file."""
    with open(JSON_LOG_FILE, 'w', encoding='utf-8') as json_file:
        json.dump(report_data, json_file, indent=4, ensure_ascii=False)
    console.print(f"\n[bold green]JSON report saved to:[/bold green] {JSON_LOG_FILE}")

# Run the process
if __name__ == "__main__":
    explain_process()
    scan_for_unsigned_apps()
    summarize_results()
    save_json_report()
    
    final_message = (
        "[bold green]Unsigned app scan completed.[/bold green]\n\n"
        f"Detailed report saved at: {JSON_LOG_FILE}\n"
        "Thank you for using GUARDSTICK."
    )
    console.print(Panel.fit(final_message, border_style="green"))