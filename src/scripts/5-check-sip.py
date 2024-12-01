import os
from datetime import datetime
import json
import subprocess

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
    """Save data to a JSON file with the appropriate filename."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return report_file

def explain_process():
    """Return explanation of the process for logging."""
    return {
        "log_type": "info",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "message": "System Integrity Protection (SIP) check is about to start. SIP prevents unauthorized modifications to system files."
    }

def check_sip_status():
    """Check SIP status and return results."""
    sip_status = subprocess.run(["csrutil", "status"], capture_output=True, text=True).stdout.strip()
    return {
        "status": sip_status,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "summary": "SIP is enabled" if "enabled" in sip_status.lower() else "SIP is disabled. Your system may be vulnerable."
    }

def generate_sip_report():
    """Generate a SIP status report in JSON format."""
    # Metadata
    metadata = {
        "scan_name": "SIP Status Check",
        "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tool_name": "SIP Checker",
        "scan_duration": "Unknown"  # Placeholder, can calculate duration if needed
    }

    # Scan results
    results = check_sip_status()

    # Combine data
    report_data = {
        "scan_metadata": metadata,
        "results": [results],
        "summary": {
            "overall_status": results['summary']
        }
    }
    
    # Save the report
    report_file = save_json(report_data, "SIP_Status")
    return report_file

def main():
    """Run the SIP check process and save the report."""
    print("Starting SIP status check...")
    report_file = generate_sip_report()
    print(f"SIP status check completed. Report saved at {report_file}")

if __name__ == "__main__":
    main()