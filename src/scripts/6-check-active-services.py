import os
import subprocess
import json
from datetime import datetime

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
    with open(report_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return report_file

def check_active_services():
    """Check active services and daemons."""
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    services_list = result.stdout.strip().splitlines()

    if not services_list:
        return {
            "scan_metadata": {
                "scan_name": "Active Services Report",
                "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "tool_name": "macOS Service Checker",
                "scan_duration": "N/A"
            },
            "results": [],
            "summary": {
                "total_services": 0,
                "notes": "No active services or daemons found."
            }
        }

    results = []
    for service in services_list:
        category = "System" if "com.apple" in service else "User-defined"
        status = "Active"
        results.append({
            "service_name": service,
            "category": category,
            "status": status
        })

    return {
        "scan_metadata": {
            "scan_name": "Active Services Report",
            "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tool_name": "macOS Service Checker",
            "scan_duration": "N/A"
        },
        "results": results,
        "summary": {
            "total_services": len(results),
            "notes": "Review unnecessary or unfamiliar services for optimization."
        }
    }

def main():
    scan_data = check_active_services()
    report_file = save_json(scan_data, "Active_Services")
    print(f"Report saved at: {report_file}")

if __name__ == "__main__":
    main()