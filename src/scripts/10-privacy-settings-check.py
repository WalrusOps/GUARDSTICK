import os
import subprocess
import sys
import json
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Define output directory and JSON report file path
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../src/data/log_reports")
REPORT_FILE = os.path.join(OUTPUT_DIR, f"Privacy_Settings_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
console = Console()

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_json(data, filepath):
    """Save data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def check_tcc_database(service, description):
    """Check the TCC database for a specific service and return results."""
    try:
        command = f"""sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
                      'SELECT client, auth_value, auth_reason FROM access WHERE service="{service}";'"""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            entries = []
            for line in result.stdout.strip().splitlines():
                if '|' in line:
                    client, auth_value, auth_reason = line.split('|')
                    entries.append({
                        "app": client,
                        "authorized": auth_value,
                        "reason": auth_reason
                    })
            return {"description": description, "access": "Found", "entries": entries}
        else:
            return {"description": description, "access": "No apps found", "entries": []}
    
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error accessing TCC database for {description}: {e}[/red]")
        return {"description": description, "access": "Error", "error_message": str(e)}

def check_tcc_database_fallback(service, description):
    """Fallback to user-level TCC database for a specific service and return results."""
    try:
        command = f"""sqlite3 ~/Library/Application\\ Support/com.apple.TCC/TCC.db \
                      'SELECT client, auth_value, auth_reason FROM access WHERE service="{service}";'"""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            entries = []
            for line in result.stdout.strip().splitlines():
                if '|' in line:
                    client, auth_value, auth_reason = line.split('|')
                    entries.append({
                        "app": client,
                        "authorized": auth_value,
                        "reason": auth_reason
                    })
            return {"description": description, "access": "Found (Fallback)", "entries": entries}
        else:
            return {"description": description, "access": "No apps found (Fallback)", "entries": []}
    
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error accessing user-level TCC database for {description}: {e}[/red]")
        return {"description": description, "access": "Error (Fallback)", "error_message": str(e)}

def main():
    # Services to check
    services = [
        ("kTCCServiceCamera", "Camera"),
        ("kTCCServiceMicrophone", "Microphone"),
        ("kTCCServiceLocation", "Location Services"),
        ("kTCCServiceSystemPolicyAllFiles", "Full Disk Access"),
        ("kTCCServiceAccessibility", "Accessibility"),
        ("kTCCServiceScreenCapture", "Screen Recording")
    ]

    # JSON structure to store results
    audit_results = {
        "audit_metadata": {
            "scan_name": "Privacy Settings Audit",
            "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tool_name": "Privacy Checker",
        },
        "results": []
    }

    total_steps = len(services)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("Running privacy audit...", total=total_steps)
        
        for i, (service, description) in enumerate(services, start=1):
            progress.update(task, description=f"Step {i}/{total_steps}: Checking {description}")
            console.print(f"[cyan]Checking {description} Access[/cyan]")
            
            # Check database and store result
            result = check_tcc_database(service, description)
            
            # If primary method fails, fallback
            if result["access"] == "Error":
                console.print(f"[yellow]Falling back to user-level database for {description}[/yellow]")
                result = check_tcc_database_fallback(service, description)
            
            audit_results["results"].append(result)
            progress.advance(task)

    # Save audit results as JSON
    save_json(audit_results, REPORT_FILE)
    console.print(f"\n[green]Privacy audit completed. Report saved at:[/green] [bold magenta]{REPORT_FILE}[/bold magenta]")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[red]This script requires administrative privileges.[/red]")
        sys.exit(1)
    
    main()