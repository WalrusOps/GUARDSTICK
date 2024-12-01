#!/usr/bin/env python3

import os
import subprocess
import shutil
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

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

class SecurityUpdateChecker:
    def __init__(self):
        self.total_steps = 2
        self.results = {
            "macOS_updates": None,
            "homebrew_updates": None
        }

    def explain_process(self):
        """Explain the process of security update check"""
        console.print(Panel(
            "[cyan]Security Update Status Checker[/cyan]\n"
            "This script will check for available security updates on your system.\n"
            "It will perform the following checks:\n"
            " - macOS system and version updates\n"
            " - Application updates (including Homebrew)\n"
            "\nRegular updates help protect your system from known vulnerabilities.\n",
            title="Security Update Status Check",
            border_style="cyan"
        ))

    def check_macos_version(self):
        """Check for macOS system and version updates"""
        console.print("\n[bold]Step 1: Checking macOS Version and Available Updates[/bold]")
        try:
            # Get current macOS version
            current_version = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True).stdout.strip()
            console.print(f"[green]Current macOS Version: {current_version}[/green]")

            # Run the softwareupdate command to list available updates
            update_info = subprocess.run(["softwareupdate", "-l"], capture_output=True, text=True).stdout

            if "No new software available" in update_info:
                console.print("[green]No macOS security updates available.[/green]")
                self.results["macOS_updates"] = {
                    "current_version": current_version,
                    "updates_available": False,
                    "update_details": None
                }
            else:
                console.print("[yellow]Available macOS updates detected:[/yellow]")
                console.print(update_info)

                # Extract the latest version info if available
                latest_version = "\n".join([line for line in update_info.splitlines() if "macOS" in line])
                self.results["macOS_updates"] = {
                    "current_version": current_version,
                    "updates_available": True,
                    "update_details": update_info.strip(),
                    "latest_version": latest_version
                }
        except Exception as e:
            console.print(f"[red]Error checking macOS version: {str(e)}[/red]")
            self.results["macOS_updates"] = {"error": str(e)}

        console.print("\n[cyan]macOS Version Check - Completed[/cyan]\n")

    def check_homebrew_updates(self):
        """Check for Homebrew updates"""
        console.print("\n[bold]Step 2: Checking for Homebrew Security Updates[/bold]")
        if shutil.which("brew"):
            try:
                # Update Homebrew package list
                console.print("Updating Homebrew package list...")
                subprocess.run(["brew", "update"], capture_output=True, text=True)

                # Check for outdated packages with security updates
                outdated_brew = subprocess.run(["brew", "outdated", "--greedy", "--verbose"], capture_output=True, text=True).stdout
                security_updates = [line for line in outdated_brew.splitlines() if "security" in line.lower()]

                if security_updates:
                    console.print("[yellow]Outdated Homebrew packages with security updates detected:[/yellow]")
                    for update in security_updates:
                        console.print(f"[red]{update}[/red]")
                    self.results["homebrew_updates"] = {
                        "updates_available": True,
                        "update_details": security_updates
                    }
                else:
                    console.print("[green]No outdated Homebrew packages with security updates detected.[/green]")
                    self.results["homebrew_updates"] = {
                        "updates_available": False,
                        "update_details": None
                    }
            except Exception as e:
                console.print(f"[red]Error checking Homebrew updates: {str(e)}[/red]")
                self.results["homebrew_updates"] = {"error": str(e)}
        else:
            console.print("[red]Homebrew is not installed on this system.[/red]")
            self.results["homebrew_updates"] = {
                "updates_available": False,
                "error": "Homebrew is not installed."
            }

        console.print("\n[cyan]Homebrew Security Updates Check - Completed[/cyan]\n")

    def summarize_results(self):
        """Summarize the results of the security update check"""
        console.print("\n[bold cyan]═══ Summary of Security Update Status Check ═══[/bold cyan]")

        # Save results to JSON
        report_file = save_json(self.results, "Security_Update_Status")
        console.print(f"[green]Security update status report saved to:[/green] [cyan]{report_file}[/cyan]")

    def perform_check(self):
        """Perform all security update checks"""
        self.explain_process()

        # Step 1: Check macOS version and updates
        self.check_macos_version()

        # Step 2: Check Homebrew updates
        self.check_homebrew_updates()

        # Summarize results
        self.summarize_results()

def main():
    checker = SecurityUpdateChecker()
    checker.perform_check()

if __name__ == "__main__":
    main()