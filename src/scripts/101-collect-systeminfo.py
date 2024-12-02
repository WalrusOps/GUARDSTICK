import os
import subprocess
import hashlib
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

# Setup
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/data/log_reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)
HASH_FILE = os.path.join(REPORTS_DIR, f"executable_hashes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

console = Console()

class SystemExecutableHasher:
    def __init__(self):
        self.directories = ["/Applications", "/usr/local/bin", "/usr/bin", os.path.expanduser("~/bin")]
        self.report_data = {
            "scan_time": datetime.now().isoformat(),
            "directories_scanned": self.directories,
            "hashes": []
        }

    def hash_executables(self):
        """Hash executable files in system directories"""
        for directory in self.directories:
            try:
                # Find executables in directory
                result = subprocess.run(
                    ["find", directory, "-type", "f", "-perm", "+111"], 
                    capture_output=True, 
                    text=True
                )
                files = [f for f in result.stdout.strip().split("\n") if f]
                
                # Calculate hashes
                for file in files:
                    if os.path.isfile(file):
                        try:
                            with open(file, "rb") as f:
                                hash_value = hashlib.sha256(f.read()).hexdigest()
                                self.report_data["hashes"].append({
                                    "file": file,
                                    "hash": hash_value
                                })
                        except Exception as e:
                            console.print(f"[red]Error hashing {file}: {str(e)}[/red]")
                            
            except Exception as e:
                console.print(f"[red]Error scanning {directory}: {str(e)}[/red]")

        # Save results
        with open(HASH_FILE, 'w') as f:
            json.dump(self.report_data, f, indent=4)

        console.print(f"\n[green]Scan complete. Found {len(self.report_data['hashes'])} executables")
        console.print(f"Results saved to: {HASH_FILE}")

def main():
    console.print(Panel("[bold]System Executable Hash Scanner[/bold]", border_style="blue"))
    hasher = SystemExecutableHasher()
    hasher.hash_executables()

if __name__ == "__main__":
    main()