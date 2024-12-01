import os
import subprocess
import signal
from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt

# Directory setup
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Console for rich output
console = Console()

# Abort flag
abort_scan = False

# Handle SIGINT to abort scans gracefully
def signal_handler(signal, frame):
    global abort_scan
    abort_scan = True
    console.print("\n[bold red]Scan aborted. Returning to the main menu...[/bold red]")

signal.signal(signal.SIGINT, signal_handler)

def generate_report_filename(scan_type):
    """Generate a timestamped JSON report filename."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{scan_type}_Report_{timestamp}.json"

def save_json(data, scan_type):
    """Save audit results as a JSON file."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as f:
        json.dump(data, f, indent=4)
    return report_file

def explain_process():
    """Display the purpose of the audit."""
    console.print(Panel(
        "[bold cyan]Advanced macOS User Account Audit[/bold cyan]\n"
        "This script performs checks on:\n"
        "- Account configurations and permissions\n"
        "- Login history and security policies\n"
        "- File access rights and startup items", border_style="cyan"))

def collect_user_details(user):
    """Gather user account details."""
    details = {
        "username": user,
        "full_name": subprocess.getoutput(f"dscl . -read /Users/{user} RealName").replace("RealName: ", ""),
        "user_id": subprocess.getoutput(f"dscl . -read /Users/{user} UniqueID").replace("UniqueID: ", ""),
        "group_id": subprocess.getoutput(f"dscl . -read /Users/{user} PrimaryGroupID").replace("PrimaryGroupID: ", ""),
        "home_directory": subprocess.getoutput(f"dscl . -read /Users/{user} NFSHomeDirectory").replace("NFSHomeDirectory: ", ""),
        "login_shell": subprocess.getoutput(f"dscl . -read /Users/{user} UserShell").replace("UserShell: ", "")
    }
    return details

def check_sudo_access(user):
    """Check if the user has sudo privileges."""
    result = subprocess.getoutput(f"sudo -l -U {user} 2>/dev/null")
    has_sudo = "User may run the following commands" in result
    return {"sudo_privileges": has_sudo, "sudo_details": result}

def check_security_policies(user):
    """Check security policies for the user."""
    pw_policy = subprocess.getoutput(f"pwpolicy -u {user} -getaccountpolicies")
    login_settings = subprocess.getoutput("defaults read /Library/Preferences/com.apple.loginwindow")
    return {"password_policy": pw_policy, "login_window_settings": login_settings}

def check_file_access(user):
    """Check file access permissions for important directories."""
    home_dir = subprocess.getoutput(f"dscl . -read /Users/{user} NFSHomeDirectory").replace("NFSHomeDirectory: ", "")
    access_permissions = {}
    if os.path.isdir(home_dir):
        important_dirs = ["Documents", "Downloads", "Library", ".ssh"]
        for directory in important_dirs:
            path = os.path.join(home_dir, directory)
            if os.path.isdir(path):
                access_permissions[directory] = subprocess.getoutput(f"ls -ldh {path}")
    return {"file_access_permissions": access_permissions}

def check_login_items(user):
    """Check the user's startup items."""
    home_dir = subprocess.getoutput(f"dscl . -read /Users/{user} NFSHomeDirectory").replace("NFSHomeDirectory: ", "")
    login_items = {}
    launch_agents_dir = os.path.join(home_dir, "Library/LaunchAgents")
    if os.path.isdir(launch_agents_dir):
        login_items = subprocess.getoutput(f"ls -la {launch_agents_dir}")
    return {"login_items": login_items}

def audit_user(user, progress: Progress, task_id: TaskID):
    """Run all audit checks for a user account and return results."""
    progress.update(task_id, description=f"Auditing {user}", advance=1)
    details = collect_user_details(user)
    sudo_access = check_sudo_access(user)
    security_policies = check_security_policies(user)
    file_access = check_file_access(user)
    login_items = check_login_items(user)

    return {
        "user_details": details,
        "sudo_access": sudo_access,
        "security_policies": security_policies,
        "file_access": file_access,
        "login_items": login_items
    }

def main():
    explain_process()

    # List all valid users
    user_list = [user for user in subprocess.getoutput("dscl . -list /Users | grep -v '^_'").splitlines()]
    audit_results = []

    # Begin audit with progress tracking
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "{task.completed}/{task.total}",
        "• Elapsed:",
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("Auditing users...", total=len(user_list))

        for user in user_list:
            if abort_scan:
                break
            result = audit_user(user, progress, task)
            audit_results.append(result)
            progress.update(task, advance=1)

    # Save results to JSON
    report_file = save_json(audit_results, "User_Audit")
    console.print(Panel(
        f"Audit completed. Reports are available at:\n[bold magenta]{report_file}[/bold magenta]",
        border_style="green"
    ))

if __name__ == "__main__":
    main()