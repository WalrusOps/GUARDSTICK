#!/usr/bin/env python3

import os
import subprocess
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import platform

# Initialize console
console = Console()

# Set up directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Function to save results as JSON
def save_as_json(data, scan_type):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{scan_type}_Report_{timestamp}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    console.print(f"Results saved to [cyan]{filepath}[/cyan]")

class RansomwareMonitor:
    def __init__(self):
        self.scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.results = {}

    def explain_process(self):
        console.print(Panel(
            "Ransomware File System Monitor\n"
            "This script monitors your system for ransomware activity.",
            title="Ransomware Monitoring",
            border_style="cyan"
        ))

    def check_unauthorized_encryption(self):
        console.print("\n[bold]Checking for Unauthorized File Encryption[/bold]")
        scan_data = {
            "scan_metadata": {
                "scan_name": "Unauthorized Encryption Check",
                "scan_date": self.scan_date,
                "tool_name": "RansomwareMonitor",
            },
            "results": [],
            "summary": {}
        }

        directories = [os.path.expanduser("~")]
        entropy_threshold = 7.5  # Threshold for high entropy

        for dir_path in directories:
            try:
                # Find recently modified files
                recent_files = subprocess.run(
                    ["find", dir_path, "-type", "f", "-mtime", "-1"],
                    capture_output=True, text=True
                ).stdout.splitlines()

                for file in recent_files:
                    try:
                        # Calculate file entropy
                        entropy = self.calculate_entropy(file)
                        if entropy > entropy_threshold:
                            scan_data["results"].append({
                                "file_path": file,
                                "entropy": entropy,
                                "status": "High Entropy - Potential Encryption"
                            })
                    except Exception:
                        continue
            except Exception as e:
                console.print(f"[red]Error scanning {dir_path}: {str(e)}[/red]")

        scan_data["summary"]["total_files_scanned"] = len(recent_files)
        scan_data["summary"]["potential_encrypted_files"] = len(scan_data["results"])

        save_as_json(scan_data, "Unauthorized_Encryption")

    def calculate_entropy(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
            if not data:
                return 0
            import math
            from collections import Counter
            counter = Counter(data)
            total = len(data)
            entropy = -sum((count / total) * math.log2(count / total) for count in counter.values())
            return entropy

    def detect_ransom_notes(self):
        console.print("\n[bold]Detecting Ransom Notes[/bold]")
        scan_data = {
            "scan_metadata": {
                "scan_name": "Ransom Note Detection",
                "scan_date": self.scan_date,
                "tool_name": "RansomwareMonitor",
            },
            "results": [],
            "summary": {}
        }

        ransom_note_names = ["README_DECRYPT.txt", "DECRYPT_INSTRUCTIONS.html", "DECRYPT_FILES.html"]
        for note_name in ransom_note_names:
            try:
                found_notes = subprocess.run(
                    ["find", os.path.expanduser("~"), "-name", note_name],
                    capture_output=True, text=True
                ).stdout.splitlines()
                for note in found_notes:
                    scan_data["results"].append({
                        "file_path": note,
                        "note_name": note_name,
                        "status": "Potential Ransom Note Detected"
                    })
            except Exception as e:
                console.print(f"[red]Error searching for {note_name}: {str(e)}[/red]")

        scan_data["summary"]["total_notes_found"] = len(scan_data["results"])
        save_as_json(scan_data, "Ransom_Note_Detection")

    def check_unusual_processes(self):
        console.print("\n[bold]Checking for Unusual Processes[/bold]")
        scan_data = {
            "scan_metadata": {
                "scan_name": "Unusual Process Check",
                "scan_date": self.scan_date,
                "tool_name": "RansomwareMonitor",
            },
            "results": [],
            "summary": {}
        }

        try:
            if platform.system() == "Darwin":
                process_output = subprocess.run(
                    ["ps", "-Ao", "pid,command,%cpu,%mem"],
                    capture_output=True, text=True
                ).stdout
            else:
                process_output = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True, text=True
                ).stdout

            for line in process_output.splitlines()[1:]:
                if "encrypt" in line.lower() or "ransom" in line.lower():
                    scan_data["results"].append({
                        "process_info": line.strip(),
                        "status": "Suspicious Process Detected"
                    })
        except Exception as e:
            console.print(f"[red]Error checking processes: {str(e)}[/red]")

        scan_data["summary"]["total_suspicious_processes"] = len(scan_data["results"])
        save_as_json(scan_data, "Unusual_Process_Check")

    def check_persistence_mechanisms(self):
        console.print("\n[bold]Checking Persistence Mechanisms[/bold]")
        scan_data = {
            "scan_metadata": {
                "scan_name": "Persistence Mechanism Check",
                "scan_date": self.scan_date,
                "tool_name": "RansomwareMonitor",
            },
            "results": [],
            "summary": {}
        }

        persistence_paths = [
            "/Library/LaunchAgents",
            "/Library/LaunchDaemons",
            os.path.expanduser("~/Library/LaunchAgents")
        ]

        for path in persistence_paths:
            try:
                files = os.listdir(path)
                for file in files:
                    full_path = os.path.join(path, file)
                    scan_data["results"].append({
                        "file_path": full_path,
                        "status": "Persistence Mechanism Detected"
                    })
            except Exception:
                continue

        scan_data["summary"]["total_persistence_files"] = len(scan_data["results"])
        save_as_json(scan_data, "Persistence_Mechanism_Check")

    def perform_monitoring(self):
        self.explain_process()
        self.check_unauthorized_encryption()
        self.detect_ransom_notes()
        self.check_unusual_processes()
        self.check_persistence_mechanisms()

def main():
    monitor = RansomwareMonitor()
    monitor.perform_monitoring()

if __name__ == "__main__":
    main()