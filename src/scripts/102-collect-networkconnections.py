import os
import re
import requests
import json

# Define report file path directly
REPORT_FILE = os.path.join(os.path.dirname(__file__), "../../src/data/log_reports/network_connections_report.json")

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

def get_country_from_ip(ip_address):
    """Retrieve the country for a given IP address using an IP geolocation API and spell out the full country name."""
    if ip_address.startswith("127."):
        return "Loopback"
    elif ip_address.startswith("192.168."):
        return "Localhost"

    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            data = response.json()
            country_name = data.get("country_name", data.get("country", "Unknown"))
            return country_name
        return "Unknown"
    except Exception:
        return "Unknown"

def get_application_name(local_ip, local_port):
    """Get the application name using lsof command for a given local IP and port."""
    try:
        lsof_output = os.popen(f"lsof -iTCP:{local_port} -sTCP:ESTABLISHED -n -P").readlines()
        for line in lsof_output:
            match = re.search(r'(\S+)\s+\d+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+.*', line)
            if match:
                return match.group(1)
        return "Unknown"
    except Exception:
        return "Unknown"

def parse_netstat_output():
    """Parse netstat output to extract relevant connection details."""
    connections = []

    netstat_output = os.popen("netstat -anp tcp").readlines()

    for line in netstat_output:
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)\s+(\d+\.\d+\.\d+\.\d+)\.(\d+)\s+(\w+)', line)
        if match:
            local_ip = match.group(1)
            local_port = match.group(2)
            foreign_ip = match.group(3)
            foreign_port = match.group(4)
            state = match.group(5)

            app_name = get_application_name(local_ip, local_port)
            country = get_country_from_ip(foreign_ip)

            connections.append({
                "Local Address": f"{local_ip}:{local_port}",
                "Foreign Address": f"{foreign_ip}:{foreign_port}",
                "State": state,
                "Application": app_name,
                "Country": country
            })

    return connections

def save_to_json(connections):
    """Save connection details to a JSON file."""
    with open(REPORT_FILE, "w") as f:
        json.dump(connections, f, indent=4)

def main():
    connections = parse_netstat_output()
    if connections:
        save_to_json(connections)

if __name__ == "__main__":
    main()