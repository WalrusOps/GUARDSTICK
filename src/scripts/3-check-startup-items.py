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
report_filename = f"Unusual_Startup_Items_Report_{timestamp}.json"
JSON_LOG_FILE = os.path.join(REPORTS_DIR, report_filename)

# Initialize data structure for JSON report
report_data = {
    "startup_items": [],
    "suspicious_items": [],
    "exported_items": []
}

# Initialize rich console
console = Console()

def log_to_json(section, data):
    """Log messages to the JSON report data structure."""
    report_data[section].append(data)

def explain_process():
    """Displays the script's purpose using a rich panel."""
    panel_content = (
        "[bold magenta]🔍 Unusual macOS Startup Items Check 🔍[/bold magenta]\n\n"
        "This script inspects macOS startup items and launch agents/daemons.\n\n"
        "It provides details on:\n"
        "- Items starting automatically at boot\n"
        "- Potentially harmful or suspicious items\n\n"
        "The results will be logged for detailed review.\n"
    )
    console.print(Panel.fit(panel_content, border_style="magenta"))
    log_to_json("startup_items", {"description": panel_content})

def check_startup_items():
    """Checks startup items in common directories."""
    console.print("[bold cyan]Step 1: Checking Startup Items[/bold cyan]")
    log_to_json("startup_items", {"step": "Checking Startup Items"})

    startup_dirs = [
        "/Library/StartupItems",
        "/System/Library/StartupItems",
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
        os.path.expanduser("~/Library/LaunchAgents"),
        os.path.expanduser("~/Library/LaunchDaemons")
    ]

    table = Table(title="Startup Items", show_header=True, header_style="bold blue")
    table.add_column("Directory", style="bold green")
    table.add_column("Items", style="cyan", justify="left")

    for directory in startup_dirs:
        if os.path.isdir(directory):
            files = subprocess.run(["ls", "-la", directory], capture_output=True, text=True)
            table.add_row(directory, files.stdout or "No items found")
            log_to_json("startup_items", {"directory": directory, "items": files.stdout.strip()})
        else:
            table.add_row(directory, "[red]Directory does not exist[/red]")
            log_to_json("startup_items", {"directory": directory, "items": "Directory does not exist"})
    
    console.print(table)
    log_to_json("startup_items", {"status": "Startup items check completed"})

def flag_suspicious_items():
    """Flags potentially suspicious startup items."""
    console.print("[bold cyan]Step 2: Identifying Suspicious Items[/bold cyan]")
    log_to_json("suspicious_items", {"step": "Identifying Suspicious Items"})

    suspicious_dirs = [
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
        os.path.expanduser("~/Library/LaunchAgents"),
        os.path.expanduser("~/Library/LaunchDaemons")
    ]

    suspicious_table = Table(title="Suspicious Startup Items", show_header=True, header_style="bold red")
    suspicious_table.add_column("Suspicious Item", style="yellow")

    for directory in suspicious_dirs:
        if os.path.isdir(directory):
            for item in os.listdir(directory):
                if item.endswith(".plist"):
                    suspicious_item = os.path.join(directory, item)
                    suspicious_table.add_row(suspicious_item)
                    log_to_json("suspicious_items", {"suspicious_item": suspicious_item})

    if suspicious_table.row_count > 0:
        console.print(suspicious_table)
    else:
        console.print("[green]No suspicious items detected.[/green]")
        log_to_json("suspicious_items", {"status": "No suspicious items detected"})

def export_startup_items():
    """Exports the list of startup items for review."""
    console.print("[bold cyan]Step 3: Exporting Startup Items[/bold cyan]")
    log_to_json("exported_items", {"step": "Exporting Startup Items"})

    startup_dirs = [
        "/Library/StartupItems",
        "/System/Library/StartupItems",
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
        os.path.expanduser("~/Library/LaunchAgents"),
        os.path.expanduser("~/Library/LaunchDaemons")
    ]

    for directory in track(startup_dirs, description="Exporting startup items..."):
        if os.path.isdir(directory):
            files = subprocess.run(["ls", "-la", directory], capture_output=True, text=True)
            log_to_json("exported_items", {"directory": directory, "items": files.stdout.strip()})

    console.print("[green]The full list of startup items has been saved in the log.[/green]")
    log_to_json("exported_items", {"status": "The full list of startup items has been saved in the log"})

def save_json_report():
    """Save the report data to a JSON file."""
    with open(JSON_LOG_FILE, 'w', encoding='utf-8') as json_file:
        json.dump(report_data, json_file, indent=4, ensure_ascii=False)
    console.print(f"\n[bold green]JSON report saved to:[/bold green] {JSON_LOG_FILE}")

def main():
    explain_process()
    check_startup_items()
    flag_suspicious_items()
    export_startup_items()
    save_json_report()

    summary_panel = (
        "[bold green]Unusual Startup Items Check Completed.[/bold green]\n\n"
        f"Report saved at: {JSON_LOG_FILE}\n"
        "Thank you for using GUARDSTICK."
    )
    console.print(Panel.fit(summary_panel, border_style="green"))

if __name__ == "__main__":
    main()