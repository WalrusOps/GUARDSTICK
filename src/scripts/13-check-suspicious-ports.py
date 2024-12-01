import os
import subprocess
import json
from datetime import datetime

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
    """Save data to a JSON file with the appropriate filename."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return report_file

def get_ip_info(ip):
    """Retrieve IP information using whois."""
    if ip in ("127.0.0.1", "::1", "*"):
        return "INTERNAL", "Local System", "N/A"
    
    if ip.startswith(("192.168", "10.", "172.")):
        return "INTERNAL", "Private Network", "N/A"
    
    try:
        whois_data = subprocess.check_output(['whois', ip], stderr=subprocess.DEVNULL).decode()
        country = next((line.split(": ")[1] for line in whois_data.splitlines() if "country" in line.lower()), "Unknown")
        org = next((line.split(": ")[1] for line in whois_data.splitlines() if "orgname" in line.lower()), "Unknown")
        netname = next((line.split(": ")[1] for line in whois_data.splitlines() if "netname" in line.lower()), "N/A")
        return country, org, netname
    except Exception:
        return "Unknown", "Unknown", "N/A"

def clean_program_name(full_name):
    """Clean and format the program name."""
    base_name = full_name.split('/')[-1]
    clean_name = base_name.replace('-bin', '').replace('.app', '').strip()
    return clean_name if clean_name else "Unknown"

def scan_connections():
    """Scan network connections and gather data for JSON output."""
    connections_data = []

    command = "lsof -i -n -P | grep ESTABLISHED"
    connections = subprocess.run(command, shell=True, capture_output=True, text=True).stdout.strip().splitlines()

    for line in connections:
        try:
            # Extract the program name, PID, user, and connection info
            fields = line.split()
            program_name = fields[0]
            pid = fields[1]
            user = fields[2]
            connection_info = fields[8]  # Adjust index based on your system's output
            
            if "->" not in connection_info:
                continue

            remote_addr = connection_info.split("->")[1]
            if ":" in remote_addr:
                remote_ip, remote_port = remote_addr.split(":")
            else:
                continue
            
            # Skip if it's localhost or internal IP
            if remote_ip in ("127.0.0.1", "*"):
                continue
            
            # Get IP information
            country, org, netname = get_ip_info(remote_ip)
            clean_name = clean_program_name(program_name)

            # Append to connections data
            connections_data.append({
                "ip_address": remote_ip,
                "port": remote_port,
                "country": country,
                "organization": org,
                "network": netname,
                "application": clean_name,
                "user": user,
            })
        except (ValueError, IndexError):
            continue

    return connections_data

def generate_network_report():
    """Generate a network connections report in JSON format."""
    # Metadata
    metadata = {
        "scan_name": "Network Connections",
        "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "tool_name": "Network Scanner",
    }

    # Scan results
    results = scan_connections()

    # Combine data
    report_data = {
        "scan_metadata": metadata,
        "results": results,
        "summary": {
            "total_connections": len(results),
            "internal_connections": sum(1 for r in results if r["country"] == "INTERNAL"),
            "external_connections": sum(1 for r in results if r["country"] != "INTERNAL")
        }
    }

    # Save the report
    report_file = save_json(report_data, "Network_Connections")
    return report_file

def main():
    """Run the network connections scan and save the report."""
    print("Starting network connections scan...")
    report_file = generate_network_report()
    print(f"Network connections scan completed. Report saved at {report_file}")

if __name__ == "__main__":
    main()