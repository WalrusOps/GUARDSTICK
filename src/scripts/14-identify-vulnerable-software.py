import os
import subprocess
import json
from datetime import datetime
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

# Define directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
EXPLOITS_DB_DIR = os.path.join(DATA_DIR, "Exploit_DB")
EXPLOITS_CSV = os.path.join(EXPLOITS_DB_DIR, "files_exploits.csv")
SHELLCODES_CSV = os.path.join(EXPLOITS_DB_DIR, "files_shellcodes.csv")
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

def is_exploit_db_populated():
    """Check if the Exploit-DB directory is populated."""
    return os.path.isdir(EXPLOITS_DB_DIR) and os.path.isfile(EXPLOITS_CSV) and os.path.isfile(SHELLCODES_CSV)

def download_exploit_db():
    """Download the Exploit-DB database."""
    console.print("[yellow]Downloading Exploit-DB database...[/yellow]")
    subprocess.run(["git", "clone", "https://gitlab.com/exploit-database/exploitdb.git", EXPLOITS_DB_DIR], check=True)
    console.print("[green]Exploit-DB database downloaded successfully.[/green]")

def extract_versions(title):
    """Extract vulnerable versions from title."""
    versions = []
    if "<= " in title:
        versions.append(f"Version {title.split('<= ')[1].split()[0]} and below")
    elif "< " in title:
        versions.append(f"Below version {title.split('< ')[1].split()[0]}")
    elif any(char.isdigit() for char in title):
        versions.append(f"Version {title.split()[0]}")
    return versions

def search_vulnerabilities(software, version, vulnerabilities):
    """Search for vulnerabilities in the Exploit-DB database."""
    found_vulnerabilities = []
    search_term = f'"{software}"'
    console.print(f"[blue]Scanning: {software} {version}[/blue]")

    if os.path.isfile(EXPLOITS_CSV):
        matches = subprocess.run(["grep", "-i", search_term, EXPLOITS_CSV], capture_output=True, text=True).stdout.strip()
        if matches:
            for match in matches.splitlines():
                parts = match.split(',')
                title = parts[2]  # Assuming title is the 3rd column
                exploit_id = parts[0]
                versions = extract_versions(title)

                found_vulnerabilities.append({
                    "id": exploit_id,
                    "title": title,
                    "url": f"https://www.exploit-db.com/exploits/{exploit_id}",
                    "vulnerable_versions": versions
                })

            vulnerabilities.extend(found_vulnerabilities)

    return found_vulnerabilities

def scan_applications(search_path, vulnerabilities):
    """Scan applications in a directory for vulnerabilities."""
    console.print(f"[cyan]Scanning applications in {search_path}...[/cyan]")
    apps = subprocess.run(["find", search_path, "-name", "*.app", "-maxdepth", "1"], 
                          capture_output=True, text=True).stdout.strip().splitlines()

    for app_path in apps:
        app_name = os.path.basename(app_path).replace('.app', '')
        version = ""
        if os.path.isfile(os.path.join(app_path, "Contents", "Info.plist")):
            version = subprocess.run(["defaults", "read", os.path.join(app_path, "Contents", "Info"), 
                                      "CFBundleShortVersionString"], capture_output=True, text=True).stdout.strip()
            if not version:
                version = subprocess.run(["defaults", "read", os.path.join(app_path, "Contents", "Info"), 
                                          "CFBundleVersion"], capture_output=True, text=True).stdout.strip()
                
            if version:
                search_vulnerabilities(app_name, version, vulnerabilities)

def check_homebrew_packages(vulnerabilities):
    """Check installed Homebrew packages for vulnerabilities."""
    if subprocess.call(["command", "-v", "brew"], stdout=subprocess.DEVNULL) == 0:
        console.print("[cyan]Scanning Homebrew packages...[/cyan]")
        brew_output = subprocess.run(["brew", "list", "--versions"], 
                                     capture_output=True, text=True).stdout.strip().splitlines()
        
        for line in brew_output:
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    app_name = parts[0]
                    version = parts[1]
                    search_vulnerabilities(app_name, version, vulnerabilities)

def main():
    # Ensure Exploit-DB is available
    if not is_exploit_db_populated():
        download_exploit_db()

    # Initialize vulnerability tracking
    vulnerabilities = []

    # Scan directories and Homebrew packages
    scan_applications("/Applications", vulnerabilities)
    scan_applications("/System/Applications", vulnerabilities)
    scan_applications(os.path.expanduser("~/Applications"), vulnerabilities)
    check_homebrew_packages(vulnerabilities)

    # Prepare JSON report data
    report_data = {
        "scan_metadata": {
            "scan_name": "Vulnerability Scan",
            "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tool_name": "Vulnerability Scanner"
        },
        "vulnerabilities": vulnerabilities,
        "summary": {
            "total_vulnerabilities": len(vulnerabilities)
        }
    }

    # Save the report
    report_file = save_json(report_data, "Vulnerability_Scan")
    console.print(f"[green]Scan complete. Report saved to:[/green] [bold magenta]{report_file}[/bold magenta]")

if __name__ == "__main__":
    main()