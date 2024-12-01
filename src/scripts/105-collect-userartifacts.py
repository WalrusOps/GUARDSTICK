import os
import subprocess
from datetime import datetime

# Define file paths
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/data/log_reports"))
ARTIFACTS_FILE = os.path.join(REPORTS_DIR, "Forensic_Artifacts.txt")

# Ensure directories exist
os.makedirs(REPORTS_DIR, exist_ok=True)

# Function to log artifacts to a file
def log_to_file(header, content):
    with open(ARTIFACTS_FILE, "a") as f:
        f.write(f"==== {header} ====\n")
        f.write(content + "\n\n" if content.strip() else "No data found.\n\n")

# Function to analyze persistence mechanisms
def analyze_persistence():
    """Collect persistence mechanisms like launch agents and startup scripts."""
    output = []
    paths = [
        "~/Library/LaunchAgents",
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
        "/etc/rc.local",
        "/etc/cron.d",
        "/etc/init.d"
    ]
    for path in paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            result = subprocess.run(["ls", "-la", expanded_path], capture_output=True, text=True)
            output.append(f"{path}:\n{result.stdout.strip()}")
    return "\n\n".join(output)

# Function to analyze recently installed applications
def analyze_recent_installs():
    """Collect information on applications installed in the last 7 days."""
    try:
        result = subprocess.run(
            ["find", "/Applications", "-type", "d", "-mtime", "-7"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error analyzing recent installs: {str(e)}"

# Function to analyze user-specific logs
def analyze_user_logs():
    """Analyze user-specific logs for unusual behavior."""
    output = []
    user_dirs = [f"/Users/{user}" for user in os.listdir("/Users") if not user.startswith("_")]
    for user_dir in user_dirs:
        logs_path = os.path.join(user_dir, "Library", "Logs")
        if os.path.exists(logs_path):
            result = subprocess.run(["find", logs_path, "-type", "f", "-mtime", "-7"], capture_output=True, text=True)
            output.append(f"{user_dir} logs:\n{result.stdout.strip()}")
    return "\n\n".join(output)

# Function to analyze recent network connections
def analyze_network_connections():
    """Analyze recently established network connections."""
    try:
        result = subprocess.run(["netstat", "-anp", "tcp"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error analyzing network connections: {str(e)}"

# Function to analyze DNS queries
def analyze_dns_queries():
    """Analyze recent DNS queries."""
    dns_query_log = "/var/log/dnsmasq.log"  # Adjust based on system
    if os.path.exists(dns_query_log):
        try:
            result = subprocess.run(["grep", "query", dns_query_log], capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error analyzing DNS queries: {str(e)}"
    return "DNS query log not found."

# Main execution
def main():
    # Clear the previous file
    with open(ARTIFACTS_FILE, "w") as f:
        f.write(f"Forensic Artifacts Collected on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")

    # Collect forensic artifacts
    log_to_file("Persistence Mechanisms", analyze_persistence())
    log_to_file("Recently Installed Applications", analyze_recent_installs())
    log_to_file("User-Specific Logs (Last 7 Days)", analyze_user_logs())
    log_to_file("Recent Network Connections", analyze_network_connections())
    log_to_file("Recent DNS Queries", analyze_dns_queries())

if __name__ == "__main__":
    main()