import os
import subprocess
import json
from datetime import datetime
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

# Define directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# JSON report filename
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

# Console for output
console = Console()

def scan_directory(directory, description, task_id, progress, results):
    """Scan a directory for .plist files and log the results."""
    try:
        if os.path.isdir(directory):
            tasks = [f for f in os.listdir(directory) if f.endswith('.plist')]
            results["directories"].append({
                "description": description,
                "directory": directory,
                "tasks_found": tasks
            })
        else:
            results["directories"].append({
                "description": description,
                "directory": directory,
                "error": "Directory not found"
            })
        progress.update(task_id, advance=1)
    except Exception as e:
        console.print(f"[red]Error scanning {description}: {str(e)}[/red]")

def check_cron_jobs(task_id, progress, results):
    """Check user and system cron jobs."""
    try:
        # User cron jobs
        user_cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if user_cron.returncode == 0 and user_cron.stdout.strip():
            results["cron_jobs"]["user_cron"] = user_cron.stdout.strip()
        else:
            results["cron_jobs"]["user_cron"] = "No user cron jobs found"

        # System cron jobs
        if os.path.isfile("/etc/crontab"):
            with open("/etc/crontab") as f:
                content = f.read().strip()
                results["cron_jobs"]["system_cron"] = content if content else "System crontab is empty"
        else:
            results["cron_jobs"]["system_cron"] = "System crontab not found"

        progress.update(task_id, advance=1)
    except Exception as e:
        console.print(f"[red]Error checking cron jobs: {str(e)}[/red]")

def scan_periodic_tasks(task_id, progress, results):
    """Scan macOS periodic tasks."""
    try:
        periodic_dir = "/etc/periodic"
        periodic_results = []

        if os.path.isdir(periodic_dir):
            for period in ['daily', 'weekly', 'monthly']:
                period_dir = os.path.join(periodic_dir, period)
                if os.path.isdir(period_dir):
                    tasks = sorted(os.listdir(period_dir))
                    periodic_results.append({
                        "period": period,
                        "tasks": tasks
                    })
        results["periodic_tasks"] = periodic_results

        # Check periodic configurations
        periodic_configs = []
        for conf_file in ["/etc/periodic.conf", "/etc/periodic.conf.local"]:
            if os.path.isfile(conf_file):
                with open(conf_file, 'r') as f:
                    periodic_configs.append({
                        "file": conf_file,
                        "content": f.read().strip()
                    })
        results["periodic_configs"] = periodic_configs

        progress.update(task_id, advance=1)
    except Exception as e:
        console.print(f"[red]Error scanning periodic tasks: {str(e)}[/red]")

def check_login_items(task_id, progress, results):
    """Check login items."""
    try:
        # Get login items via AppleScript
        osascript_cmd = ['osascript', '-e', 'tell application "System Events" to get the name of every login item']
        result = subprocess.run(osascript_cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            results["login_items"]["application_login_items"] = [item.strip() for item in result.stdout.strip().split(',')]

        # Check Launch Services registration
        lsregister_cmd = ['/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister', '-dump']
        result = subprocess.run(lsregister_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            login_items = set()
            for line in result.stdout.split('\n'):
                if 'login-item' in line.lower() and 'CFBundleIdentifier' in line:
                    identifier = line.split('=')[1].strip().strip('";')
                    login_items.add(identifier)
            results["login_items"]["system_login_items"] = sorted(login_items)

        progress.update(task_id, advance=1)
    except Exception as e:
        console.print(f"[red]Error checking login items: {str(e)}[/red]")

def main():
    """Main function to perform task scanning."""
    # Prepare results data structure
    results = {
        "scan_metadata": {
            "scan_name": "Scheduled Tasks Check",
            "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tool_name": "Task Scanner"
        },
        "directories": [],
        "cron_jobs": {},
        "periodic_tasks": [],
        "periodic_configs": [],
        "login_items": {}
    }

    # Define scan directories
    directories = [
        ("/Library/LaunchDaemons", "System LaunchDaemons"),
        ("/Library/LaunchAgents", "System LaunchAgents"),
        (os.path.join(os.path.expanduser("~"), "Library/LaunchAgents"), "User LaunchAgents"),
        (os.path.join(os.path.expanduser("~"), "Library/LaunchDaemons"), "User LaunchDaemons")
    ]

    with Progress() as progress:
        scan_task = progress.add_task("[cyan]Scanning system...", total=len(directories) + 3)
        
        # Scan all directories
        for directory, description in directories:
            scan_directory(directory, description, scan_task, progress, results)

        # Perform additional checks
        check_cron_jobs(scan_task, progress, results)
        scan_periodic_tasks(scan_task, progress, results)
        check_login_items(scan_task, progress, results)

    # Save JSON report
    report_file = save_json(results, "Scheduled_Tasks")
    console.print(f"[green]Scan complete. Report saved to:[/green] [bold magenta]{report_file}[/bold magenta]")

if __name__ == "__main__":
    main()