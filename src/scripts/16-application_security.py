import os
import subprocess
import json
from collections import defaultdict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

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

# Define risk levels
RISKY_ENTITLEMENTS = {
    "com.apple.security.device.camera": {
        "name": "Camera Access",
        "risk_level": "High",
        "purpose": "Allows application to access device camera",
        "concerns": [
            "Can capture images/video without visible indicator",
            "Potential privacy breach if compromised"
        ]
    },
    "com.apple.security.device.microphone": {
        "name": "Microphone Access",
        "risk_level": "High",
        "purpose": "Allows application to record audio",
        "concerns": [
            "Can record audio without visible indicator",
            "Potential for unauthorized surveillance"
        ]
    },
    "com.apple.security.cs.allow-unsigned-executable-memory": {
        "name": "Unsigned Memory Execution",
        "risk_level": "Critical",
        "purpose": "Allows execution of unsigned code in memory",
        "concerns": [
            "Code injection risks",
            "Malware execution vector"
        ]
    }
}

def get_app_entitlements(app_path):
    """Retrieve entitlements for an application."""
    try:
        result = subprocess.run(
            ['codesign', '-d', '--entitlements', ':-', app_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        return ""
    except subprocess.CalledProcessError:
        return ""

def scan_applications():
    """Scan applications and return detected permissions."""
    apps_found = defaultdict(list)
    error_logs = []
    results = {"applications": [], "errors": []}

    try:
        apps = [app for app in os.listdir('/Applications') if app.endswith('.app')]
    except Exception as e:
        error_logs.append(f"Error accessing /Applications: {str(e)}")
        return results

    with Progress() as progress:
        task = progress.add_task("Scanning applications...", total=len(apps))
        
        for app in apps:
            try:
                app_path = os.path.join('/Applications', app)
                entitlements = get_app_entitlements(app_path)
                detected_permissions = []

                for ent, details in RISKY_ENTITLEMENTS.items():
                    if ent in entitlements:
                        detected_permissions.append({
                            "permission": details["name"],
                            "risk_level": details["risk_level"],
                            "purpose": details["purpose"],
                            "concerns": details["concerns"]
                        })

                if detected_permissions:
                    apps_found[app] = detected_permissions
                    results["applications"].append({
                        "app_name": app.replace('.app', ''),
                        "entitlements": detected_permissions
                    })
                progress.update(task, advance=1)

            except Exception as e:
                error_logs.append(f"Error scanning {app}: {str(e)}")

    results["errors"] = error_logs
    return results

def print_summary(results):
    """Print a summary of the scan results."""
    console.print("\n[bold cyan]═══ Application Security Analysis ═══[/bold cyan]")
    table = Table(title="Detected Application Permissions", show_header=True, header_style="bold cyan")
    table.add_column("Application", style="cyan", width=30)
    table.add_column("Permissions", style="yellow", width=40)
    table.add_column("Risk Level", justify="center", style="red", width=15)

    for app in results["applications"]:
        app_name = app["app_name"]
        permissions = "\n".join(f"• {perm['permission']}" for perm in app["entitlements"])
        max_risk = max(perm["risk_level"] for perm in app["entitlements"], key=lambda x: ["Low", "Medium", "High", "Critical"].index(x))
        table.add_row(app_name, permissions, max_risk)

    console.print(table)

    if results["errors"]:
        console.print("\n[red]Errors encountered during scan:[/red]")
        for error in results["errors"]:
            console.print(f"  • {error}")

def main():
    console.print(Panel(
        "[cyan]Application Security Scanner[/cyan]\n\n"
        "This tool scans macOS applications for sensitive permissions.\n",
        title="System Scanner", border_style="cyan"
    ))

    # Scan applications and generate results
    results = scan_applications()

    # Save results to a JSON file
    report_file = save_json(results, "Application_Security")
    console.print(f"[green]Scan complete. Report saved to:[/green] [bold magenta]{report_file}[/bold magenta]")

    # Print summary
    print_summary(results)

if __name__ == "__main__":
    main()