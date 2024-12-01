import os
import subprocess
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.layout import Layout
from rich.text import Text

# Define base and report directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))  # Root directory
SRC_DIR = os.path.join(ROOT_DIR, "src")                                        # Source directory
DATA_DIR = os.path.join(SRC_DIR, "data")                                       # Data directory
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")                            # Log reports directory
os.makedirs(REPORTS_DIR, exist_ok=True)

# Define a human-readable report filename with a timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_filename = f"Firewall_Security_Report_{timestamp}.json"
JSON_REPORT_FILE = os.path.join(REPORTS_DIR, report_filename)

console = Console()

# Initialize the data structure for JSON report
report_data = {
    "firewall_status": [],
    "logging_status": [],
    "stealth_mode_status": [],
    "application_rules": [],
    "critical_apps_status": [],
    "open_ports": [],
    "full_firewall_config": []
}

def log_to_json(section, data):
    """Log messages to the JSON report data structure."""
    report_data[section].append(data)

def display_intro():
    """Display an advanced intro panel for the firewall check."""
    intro_text = Text("Advanced macOS Firewall Security Check", style="bold magenta")
    description = ("This tool performs a comprehensive review of your macOS firewall settings.\n"
                   "It checks the following:\n"
                   "- Global firewall status\n"
                   "- Firewall logging settings\n"
                   "- Application-specific rules\n"
                   "- Stealth mode (anti-scan protection)\n"
                   "- Port configurations\n"
                   "- Full firewall export\n")
    console.print(Panel(intro_text, border_style="magenta"))
    console.print(description, style="dim")

def run_command(command, description, success_msg, error_msg, section):
    """Run a command with progress, displaying success and error messages."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        console.print(f"[green]✔ {success_msg}[/green]")
        console.print(result.stdout)
        log_to_json(section, {"description": description, "output": result.stdout.strip()})
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ {error_msg}[/red]")
        log_to_json(section, {"description": description, "error": e.stderr.strip()})

def check_firewall_status():
    console.print(Panel("[bold cyan]Step 1: Checking Global Firewall Status[/bold cyan]", border_style="cyan"))
    run_command(
        ["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
        "Global Firewall Status",
        "Firewall Status: ENABLED.",
        "Error: Unable to retrieve firewall status.",
        "firewall_status"
    )

def check_logging_status():
    console.print(Panel("[bold cyan]Step 2: Checking Firewall Logging[/bold cyan]", border_style="cyan"))
    run_command(
        ["sudo", "/usr.libexec/ApplicationFirewall/socketfilterfw", "--getloggingmode"],
        "Firewall Logging Status",
        "Firewall Logging Status: ENABLED.",
        "Error: Unable to retrieve firewall logging status.",
        "logging_status"
    )

def check_stealth_mode():
    console.print(Panel("[bold cyan]Step 3: Checking Stealth Mode[/bold cyan]", border_style="cyan"))
    run_command(
        ["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getstealthmode"],
        "Stealth Mode Status",
        "Stealth Mode: ENABLED.",
        "Error: Unable to retrieve stealth mode status.",
        "stealth_mode_status"
    )

def list_application_rules():
    console.print(Panel("[bold cyan]Step 4: Listing Application Rules[/bold cyan]", border_style="cyan"))
    run_command(
        ["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--listapps"],
        "Application Rules",
        "Application-specific firewall rules listed below.",
        "Error: Unable to list application rules.",
        "application_rules"
    )

def check_critical_apps():
    console.print(Panel("[bold cyan]Step 5: Checking Critical Applications[/bold cyan]", border_style="cyan"))
    critical_apps = ["Safari.app", "Google Chrome.app", "Remote Desktop.app", "SSH"]
    table = Table(title="Critical Applications Firewall Status", show_header=True, header_style="bold blue")
    table.add_column("Application", justify="left")
    table.add_column("Status", justify="center")

    with Progress() as progress:
        task = progress.add_task("[cyan]Checking critical apps...", total=len(critical_apps))
        for app in critical_apps:
            app_path = f"/Applications/{app}"
            result = subprocess.run(["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getappblockingstatus", app_path],
                                    capture_output=True, text=True)
            app_status = "ALLOWED" if "ALLOWED" in result.stdout else "BLOCKED or Not Found"
            table.add_row(app, f"[green]{app_status}[/green]" if "ALLOWED" in result.stdout else f"[red]{app_status}[/red]")
            log_to_json("critical_apps_status", {"application": app, "status": app_status})
            progress.update(task, advance=1)
    
    console.print(table)

def list_firewall_ports():
    console.print(Panel("[bold cyan]Step 6: Listing Open and Listening Ports[/bold cyan]", border_style="cyan"))
    run_command(
        ["sudo", "lsof", "-i", "-P"],
        "Open and Listening Ports",
        "Below are the open and listening ports.",
        "Error: Unable to list firewall ports.",
        "open_ports"
    )

def export_firewall_config():
    console.print(Panel("[bold cyan]Step 7: Exporting Full Firewall Configuration[/bold cyan]", border_style="cyan"))
    commands = [
        (["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getblockall"], "Block-All Mode Status:"),
        (["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getloggingmode"], "Logging Mode Status:"),
        (["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--listapps"], "Application Rules:")
    ]
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Exporting firewall configuration...", total=len(commands))
        for command, description in commands:
            run_command(command, description, description, f"Error: Failed to retrieve {description.lower()}", "full_firewall_config")
            progress.update(task, advance=1)

def save_json_report():
    """Save the report data to a JSON file."""
    with open(JSON_REPORT_FILE, 'w', encoding='utf-8') as json_file:
        json.dump(report_data, json_file, indent=4, ensure_ascii=False)
    console.print(f"\n[bold green]JSON report saved to:[/bold green] {JSON_REPORT_FILE}")

def main():
    # Main layout for the script's advanced design
    display_intro()
    check_firewall_status()
    check_logging_status()
    check_stealth_mode()
    list_application_rules()
    check_critical_apps()
    list_firewall_ports()
    export_firewall_config()
    save_json_report()

    console.print(Panel(f"[bold green]Firewall check completed successfully.[/bold green]\n"
                        f"Report saved at: {JSON_REPORT_FILE}", border_style="green"))

if __name__ == "__main__":
    main()