import os
import subprocess

# Define report paths
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/data/log_reports"))
NETWORK_LOG = os.path.join(REPORTS_DIR, "Advanced_Network_Monitoring.txt")

# Ensure the report directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

# Function to log results to the file
def log_results(header, content):
    """Log monitoring results with a specific header."""
    with open(NETWORK_LOG, "a") as f:
        f.write(f"{header}\n{'=' * 50}\n{content}\n\n")

# Function to list open ports and services
def check_open_ports():
    """Check for open TCP ports and associated services."""
    result = subprocess.run(["sudo", "lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"], capture_output=True, text=True)
    open_ports = result.stdout.strip()
    log_results("Open Ports and Services", open_ports if open_ports else "No open ports detected.")

# Function to check active network connections
def check_active_connections():
    """List active network connections."""
    result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
    active_connections = result.stdout.strip()
    log_results("Active Network Connections", active_connections if active_connections else "No active network connections detected.")

# Function to monitor bandwidth usage
def monitor_bandwidth_usage():
    """Monitor network bandwidth usage statistics."""
    result = subprocess.run(["netstat", "-ib"], capture_output=True, text=True)
    network_stats = result.stdout.strip()
    log_results("Network Bandwidth Usage Statistics", network_stats if network_stats else "Unable to retrieve network statistics.")

# Main execution
def main():
    # Initialize log file
    with open(NETWORK_LOG, "w") as f:
        f.write("Advanced Network Monitoring Report\n" + "=" * 50 + "\n\n")

    # Perform the checks
    check_open_ports()
    check_active_connections()
    monitor_bandwidth_usage()

if __name__ == "__main__":
    main()