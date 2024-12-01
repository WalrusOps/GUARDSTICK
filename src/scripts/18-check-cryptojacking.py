#!/usr/bin/env python3

import os
import json
import psutil
import subprocess
import tempfile
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, track

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

class CryptojackingAnalyzer:
    def __init__(self):
        self.miners = ["xmrig", "minerd", "coinhive", "crypto", "nicehash", "jsecoin", "xmr-stak", "ccminer"]
        self.scan_dirs = ["/usr/local", "/usr/bin", "/opt", "/Library"]
        self.browsers = ["Chrome", "Firefox", "Brave", "Safari"]
        self.results = {
            "cpu_usage": [],
            "miners_found": [],
            "browser_mining_activity": []
        }

    def explain_process(self):
        """Explain the process of cryptojacking analysis"""
        console.print(Panel(
            "[cyan]Cryptojacking Analyzer[/cyan]\n"
            "This script will scan your system for signs of cryptojacking.\n"
            "The following checks will be performed:\n"
            " - High CPU usage by suspicious processes\n"
            " - Known cryptojacking scripts or miners\n"
            " - Unauthorized browser-based mining activity\n"
            "\nCryptojacking can lead to high CPU usage and slow performance.\n"
            "[yellow]Ensure all suspicious activities are addressed promptly.[/yellow]",
            title="Cryptojacking Analysis Process",
            border_style="cyan"
        ))

    def check_high_cpu_usage(self):
        """Check for high CPU usage by suspicious processes"""
        suspicious_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] is not None and proc.info['cpu_percent'] > 50 and proc.info['name'] not in ["kernel_task", "WindowServer"]:
                    suspicious_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if suspicious_processes:
            self.results["cpu_usage"] = suspicious_processes
        else:
            self.results["cpu_usage"] = []

    def scan_for_cryptojacking_scripts(self):
        """Scan for known cryptojacking scripts or miners"""
        for miner in self.miners:
            for dir in self.scan_dirs:
                miner_files = subprocess.run(["find", dir, "-type", "f", "-name", f"*{miner}*"], capture_output=True, text=True).stdout.strip()
                if miner_files:
                    self.results["miners_found"].append({
                        "miner": miner,
                        "files": miner_files.split("\n")
                    })
                    break

    def check_browser_mining_activity(self):
        """Check for unauthorized browser mining activity"""
        for browser in self.browsers:
            if browser == "Chrome":
                browser_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Extensions")
            elif browser == "Firefox":
                browser_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*.default-release/extensions")
            elif browser == "Brave":
                browser_path = os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Extensions")
            elif browser == "Safari":
                browser_path = os.path.expanduser("~/Library/Safari/Extensions")

            try:
                cryptojacking_extensions = subprocess.run(["grep", "-r", "coinhive", browser_path], capture_output=True, text=True).stdout.strip()
                if cryptojacking_extensions:
                    self.results["browser_mining_activity"].append({
                        "browser": browser,
                        "activity": cryptojacking_extensions.split("\n")
                    })
            except Exception:
                pass

    def summarize_results(self):
        """Summarize and save results"""
        report_file = save_json(self.results, "Cryptojacking_Scan")
        console.print(f"\n[green]Cryptojacking scan complete. Report saved to: {report_file}[/green]")

    def perform_analysis(self):
        """Perform all cryptojacking analysis steps"""
        self.explain_process()

        with Progress() as progress:
            task = progress.add_task("[cyan]Scanning for cryptojacking...", total=3)
            self.check_high_cpu_usage()
            progress.advance(task)

            self.scan_for_cryptojacking_scripts()
            progress.advance(task)

            self.check_browser_mining_activity()
            progress.advance(task)

        self.summarize_results()

def main():
    analyzer = CryptojackingAnalyzer()
    analyzer.perform_analysis()

if __name__ == "__main__":
    main()