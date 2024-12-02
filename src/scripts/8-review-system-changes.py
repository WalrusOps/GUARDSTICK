import os
import subprocess
from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel

# Set up directories
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/data/log_reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)

console = Console()

def save_json(data):
    """Save data as JSON file."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = os.path.join(REPORTS_DIR, f"System_Changes_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(data, f, indent=4)
    return report_file

def check_logs(predicate):
    """Fetch important log entries matching the predicate."""
    cmd = ["log", "show", "--predicate", predicate, "--info", "--last", "7d"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Filter out noise and keep important entries
    important_entries = []
    for line in result.stdout.splitlines():
        # Skip common noise entries
        if any(skip in line.lower() for skip in [
            'biomeaccessservice',
            'releasing sandbox',
            'consuming sandbox',
            'getinstalledprofiles',
            'mdmclient',
            'observer'
        ]):
            continue
            
        # Keep important system events
        if any(important in line.lower() for important in [
            'installed',
            'updated',
            'deleted',
            'modified',
            'created',
            'removed',
            'error',
            'failed',
            'security',
            'warning'
        ]):
            important_entries.append(line)
    
    return important_entries

def process_scan():
    """Perform focused system change scan."""
    scan_data = {
        "scan_time": datetime.now().isoformat(),
        "system_changes": {
            "important_events": check_logs(
                'eventMessage CONTAINS[c] "installed" OR ' +
                'eventMessage CONTAINS[c] "updated" OR ' +
                'eventMessage CONTAINS[c] "deleted" OR ' +
                'eventMessage CONTAINS[c] "modified" OR ' +
                'eventMessage CONTAINS[c] "error" OR ' +
                'eventMessage CONTAINS[c] "warning" OR ' +
                'eventMessage CONTAINS[c] "security"'
            )
        }
    }
    
    # Add basic summary
    scan_data["summary"] = {
        "total_important_events": len(scan_data["system_changes"]["important_events"]),
        "status": "Changes Detected" if scan_data["system_changes"]["important_events"] else "No Significant Changes"
    }
    
    return scan_data

def main():
    console.print(Panel("[bold]Scanning for Important System Changes[/bold]", border_style="blue"))
    
    # Perform scan and save results
    report_data = process_scan()
    report_file = save_json(report_data)
    
    # Show brief summary
    console.print(f"\nFound {report_data['summary']['total_important_events']} important system changes")
    console.print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    main()