import os
import subprocess
from datetime import datetime
import json

# Set up directories and file paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
LOG_FILE = os.path.join(REPORTS_DIR, "Security_Logs.json")

def collect_relevant_logs():
    """Collect relevant security logs and save them in JSON format."""
    logs = []

    # Define relevant log predicates
    log_categories = {
        "Authentication Events": "eventMessage contains 'Authentication' AND (eventMessage contains 'failed' OR eventMessage contains 'success')",
        "Privilege Escalation": "eventMessage contains 'sudo' OR eventMessage contains 'permission denied'",
        "Application Crashes": "eventMessage contains 'crash' AND eventMessage contains 'com.apple.'",
        "Service Failures": "eventMessage contains 'service' AND eventMessage contains 'failed'",
        "Firewall or Network Issues": "eventMessage contains 'firewall' OR eventMessage contains 'blocked'",
        "Security Alerts": "eventMessage contains 'malware' OR eventMessage contains 'alert'"
    }

    # Collect logs for each category
    for category, predicate in log_categories.items():
        result = subprocess.run(
            ["log", "show", "--predicate", predicate, "--info", "--last", "24h"],
            capture_output=True, text=True
        )
        logs.append({
            "category": category,
            "predicate": predicate,
            "logs": result.stdout.strip().splitlines() if result.stdout.strip() else []
        })

    # Save logs to JSON file
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def main():
    """Main function to collect logs and store them in a structured format."""
    collect_relevant_logs()

if __name__ == "__main__":
    main()