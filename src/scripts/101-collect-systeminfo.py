#!/usr/bin/env python3

import os
import subprocess
import hashlib
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

# Initialize console
console = Console()

# Set up base directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))  # Root directory
SRC_DIR = os.path.join(ROOT_DIR, "src")                                        # Source directory
DATA_DIR = os.path.join(SRC_DIR, "data")                                       # Data directory
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")                            # Log reports directory
os.makedirs(REPORTS_DIR, exist_ok=True)

# Report file paths
HASH_FILE_TXT = os.path.join(REPORTS_DIR, "System_executable_hashes.txt")
HASH_FILE_JSON = os.path.join(REPORTS_DIR, "System_executable_hashes.json")

# Clear previous logs
with open(HASH_FILE_TXT, 'w') as f:
    f.write("")
with open(HASH_FILE_JSON, 'w') as f:
    json.dump({"metadata": {}, "hashes": []}, f, indent=4)

# Function to log messages to a file
def log_to_file(message, file_path=HASH_FILE_TXT):
    with open(file_path, 'a') as f:
        f.write(f"{message}\n")

# Function to save JSON data
def save_to_json(data, file_path=HASH_FILE_JSON):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

class SystemExecutableHasher:
    def __init__(self):
        self.directories = ["/Applications", "/usr/local/bin", "/usr/bin", os.path.expanduser("~/bin")]
        self.total_files = 0
        self.report_data = {"metadata": {}, "hashes": []}

    def explain_process(self):
        """Explain the process of system executable hashing"""
        console.print(Panel(
            "[cyan]System Executable Hash Collector[/cyan]\n"
            "This script will:\n"
            "- Find executable files in important system directories\n"
            "- Calculate their SHA-256 hash values for verification\n"
            "- Save the results in JSON and plain text formats\n",
            title="System Executable Hashing",
            border_style="cyan"
        ))

    def hash_executables(self):
        """Hash executable files in system directories"""
        console.print("\n[bold]Step 1: Hashing System Executables[/bold]")
        log_to_file("Step 1: Hashing System Executables")

        console.print("\n[bold cyan]Scanning the following directories for executables:[/bold cyan]")
        for dir in self.directories:
            console.print(f"[green] - {dir}[/green]")
            log_to_file(f"Scanning directory: {dir}")

        # Find all executables in the specified directories
        files = []
        for dir in self.directories:
            try:
                result = subprocess.run(["find", dir, "-type", "f", "-perm", "+111"], capture_output=True, text=True)
                files.extend(result.stdout.strip().split("\n"))
            except Exception as e:
                console.print(f"[red]Error scanning directory {dir}: {str(e)}[/red]")
                log_to_file(f"Error scanning directory {dir}: {str(e)}")

        files = [file for file in files if file]  # Remove empty entries
        self.total_files = len(files)

        # Add metadata to the report
        self.report_data["metadata"] = {
            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "directories_scanned": self.directories,
            "total_files_found": self.total_files,
        }

        console.print("\n[bold cyan]Now calculating SHA-256 hashes for the found executables...[/bold cyan]")
        log_to_file("Now calculating SHA-256 hashes for the found executables...")

        with Progress() as progress:
            task = progress.add_task("[cyan]Hashing executables...", total=self.total_files)

            for file in files:
                if os.path.isfile(file):
                    try:
                        with open(file, "rb") as f:
                            hash_value = hashlib.sha256(f.read()).hexdigest()
                            log_to_file(f"{file} SHA256: {hash_value}")
                            self.report_data["hashes"].append({"file": file, "hash": hash_value})
                    except Exception as e:
                        console.print(f"[red]Error hashing file {file}: {str(e)}[/red]")
                        log_to_file(f"Error hashing file {file}: {str(e)}")

                progress.update(task, advance=1)

        save_to_json(self.report_data)
        console.print(f"\n[bold green]Executable hashing completed. Results saved to:[/bold green]\n"
                      f"- [cyan]{HASH_FILE_TXT}[/cyan]\n"
                      f"- [cyan]{HASH_FILE_JSON}[/cyan]")

    def summarize_results(self):
        """Summarize the results of the executable hashing"""
        console.print("\n[bold cyan]═══ Summary of System Executable Hashing ═══[/bold cyan]")
        log_to_file("\nSummary of System Executable Hashing")
        with open(HASH_FILE_TXT, 'r') as f:
            summary = f.read()
            console.print(summary)
        console.print("\nThe system executable hashing process has been completed. You can find the detailed reports in:")
        console.print(f"- [cyan]{HASH_FILE_TXT}[/cyan]\n- [cyan]{HASH_FILE_JSON}[/cyan]")

    def perform_hashing(self):
        """Perform the hashing of system executables"""
        self.explain_process()
        self.hash_executables()
        self.summarize_results()

def main():
    hasher = SystemExecutableHasher()
    hasher.perform_hashing()

if __name__ == "__main__":
    main()