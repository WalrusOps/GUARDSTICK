import os
import subprocess
import json
import re
import requests
from datetime import datetime
import psutil
import socket
import platform
import netifaces
from rich.console import Console
from rich import print as rprint
import nmap
import scapy.all as scapy
from scapy.layers.l2 import ARP, Ether
from concurrent.futures import ThreadPoolExecutor
import ssl
import OpenSSL
import speedtest

# Initialize rich console
console = Console()

# Get absolute path to script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../src/data/log_reports"))
NETWORK_REPORT = os.path.join(REPORTS_DIR, f"network_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

# Create reports directory
console.print(f"[yellow]Creating reports directory at: {REPORTS_DIR}[/yellow]")
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_country_from_ip(ip_address):
    """Retrieve country for an IP address."""
    if not ip_address:
        return "Unknown"
        
    console.print(f"[cyan]Getting country for IP: {ip_address}[/cyan]")
    if ip_address.startswith(("127.", "192.168.", "10.", "172.16.")):
        return "Local Network"
    
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            data = response.json()
            return data.get("country_name", data.get("country", "Unknown"))
        return "Unknown"
    except Exception as e:
        console.print(f"[red]Error getting country for IP {ip_address}: {str(e)}[/red]")
        return "Unknown"

def get_application_name(local_ip, local_port):
    """Get application name for a connection."""
    try:
        cmd = f"lsof -iTCP:{local_port} -sTCP:ESTABLISHED -n -P"
        output = subprocess.check_output(cmd, shell=True).decode()
        match = re.search(r'(\S+)\s+\d+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+.*', output)
        return match.group(1) if match else "Unknown"
    except (subprocess.SubprocessError, AttributeError) as e:
        console.print(f"[red]Error getting application name: {str(e)}[/red]")
        return "Unknown"

def execute_command(command):
    """Execute system command and return output."""
    console.print(f"[cyan]Executing command: {' '.join(command)}[/cyan]")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        console.print(f"[red]Error executing command: {str(e)}[/red]")
        return f"Error: {str(e)}"

def check_open_ports():
    """Check for open TCP ports and associated services."""
    console.print("[green]Checking open ports...[/green]")
    try:
        lsof_output = execute_command(["sudo", "lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"])
        netstat_output = execute_command(["netstat", "-tuln"])
        
        return {
            "lsof_listening_ports": lsof_output,
            "netstat_listening_ports": netstat_output
        }
    except Exception as e:
        console.print(f"[red]Error checking open ports: {str(e)}[/red]")
        return {"error": str(e)}

def check_active_connections():
    """List active network connections with geolocation."""
    console.print("[green]Checking active connections...[/green]")
    connections = []
    for conn in psutil.net_connections(kind='all'):
        try:
            if conn.laddr:
                # Handle cases where laddr might be a string or a tuple
                if isinstance(conn.laddr, tuple):
                    local_ip = conn.laddr[0]
                    local_port = conn.laddr[1]
                else:
                    continue  # Skip if we can't parse the address format

                # Handle remote address
                remote_ip = None
                remote_port = None
                if conn.raddr:
                    if isinstance(conn.raddr, tuple):
                        remote_ip = conn.raddr[0]
                        remote_port = conn.raddr[1]

                connection_info = {
                    "local_address": f"{local_ip}:{local_port}",
                    "remote_address": f"{remote_ip}:{remote_port}" if remote_ip else None,
                    "status": conn.status,
                    "pid": conn.pid,
                    "process_name": psutil.Process(conn.pid).name() if conn.pid else None,
                    "country": get_country_from_ip(remote_ip) if remote_ip else None,
                    "application": get_application_name(local_ip, local_port)
                }
                connections.append(connection_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError) as e:
            console.print(f"[red]Error processing connection: {str(e)}[/red]")
            continue
    
    return connections

def get_system_network_info():
    """Get detailed system network information."""
    console.print("[green]Gathering system network information...[/green]")
    network_info = {}
    try:
        for interface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    network_info[interface] = {
                        "ip": addrs[netifaces.AF_INET][0]['addr'],
                        "netmask": addrs[netifaces.AF_INET][0]['netmask'],
                        "mac": addrs[netifaces.AF_LINK][0]['addr'] if netifaces.AF_LINK in addrs else "Unknown"
                    }
            except Exception as e:
                console.print(f"[red]Error processing interface {interface}: {str(e)}[/red]")
                continue
    except Exception as e:
        console.print(f"[red]Error getting network info: {str(e)}[/red]")
    return network_info

def monitor_bandwidth_usage():
    """Monitor bandwidth usage."""
    console.print("[green]Monitoring bandwidth usage...[/green]")
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    except Exception as e:
        console.print(f"[red]Error monitoring bandwidth: {str(e)}[/red]")
        return {"error": str(e)}

def check_dns_resolution():
    """Check DNS resolution for common domains."""
    console.print("[green]Checking DNS resolution...[/green]")
    domains = ["google.com", "facebook.com", "amazon.com", "apple.com", "microsoft.com"]
    dns_results = {}
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            dns_results[domain] = ip
        except socket.gaierror as e:
            dns_results[domain] = f"Resolution failed: {str(e)}"
    return dns_results

def check_ssl_certificates():
    """Check SSL certificates for common domains."""
    console.print("[green]Checking SSL certificates...[/green]")
    domains = ["google.com", "facebook.com", "amazon.com", "apple.com", "microsoft.com"]
    ssl_results = {}
    for domain in domains:
        try:
            cert = ssl.get_server_certificate((domain, 443))
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            ssl_results[domain] = {
                "subject": dict(x509.get_subject().get_components()),
                "issuer": dict(x509.get_issuer().get_components()),
                "version": x509.get_version(),
                "serial_number": x509.get_serial_number(),
                "not_before": x509.get_notBefore().decode(),
                "not_after": x509.get_notAfter().decode()
            }
        except Exception as e:
            ssl_results[domain] = f"Error: {str(e)}"
    return ssl_results

def check_network_performance():
    """Check network performance using speedtest-cli."""
    console.print("[green]Checking network performance...[/green]")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
        return {
            "download_speed_mbps": round(download_speed, 2),
            "upload_speed_mbps": round(upload_speed, 2),
            "ping_ms": round(ping, 2)
        }
    except Exception as e:
        console.print(f"[red]Error checking network performance: {str(e)}[/red]")
        return {"error": str(e)}

def check_wireless_info():
    """Check wireless network information."""
    console.print("[green]Checking wireless network information...[/green]")
    try:
        if platform.system() == "Darwin":  # macOS
            airport_cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
            output = subprocess.check_output(airport_cmd, shell=True).decode()
            wireless_info = {}
            for line in output.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    wireless_info[key.strip()] = value.strip()
            return wireless_info
        else:
            return {"error": "Wireless info check only supported on macOS"}
    except Exception as e:
        console.print(f"[red]Error checking wireless info: {str(e)}[/red]")
        return {"error": str(e)}

def check_firewall_status():
    """Check firewall status."""
    console.print("[green]Checking firewall status...[/green]")
    try:
        if platform.system() == "Darwin":  # macOS
            output = subprocess.check_output(["sudo", "pfctl", "-s", "info"], stderr=subprocess.STDOUT).decode()
            return "Firewall is enabled" if "Status: Enabled" in output else "Firewall is disabled"
        else:
            return "Firewall status check not implemented for this OS"
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error checking firewall status: {str(e)}[/red]")
        return "Unable to determine firewall status"

def scan_network():
    """Scan local network for devices."""
    console.print("[green]Scanning local network for devices...[/green]")
    try:
        arp = ARP(pdst="192.168.1.0/24")
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        result = scapy.srp(packet, timeout=3, verbose=0)[0]
        devices = []
        for sent, received in result:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})
        return devices
    except Exception as e:
        console.print(f"[red]Error scanning network: {str(e)}[/red]")
        return []

def perform_port_scan(ip, ports):
    """Perform a port scan on a specific IP."""
    console.print(f"[green]Performing port scan on {ip}...[/green]")
    try:
        nm = nmap.PortScanner()
        nm.scan(ip, arguments=f"-p {','.join(map(str, ports))}")
        open_ports = []
        for port in ports:
            try:
                if nm[ip]['tcp'][port]['state'] == 'open':
                    open_ports.append(port)
            except KeyError:
                continue
        return open_ports
    except Exception as e:
        console.print(f"[red]Error performing port scan: {str(e)}[/red]")
        return []

def parse_netstat_details():
    """Parse detailed netstat output."""
    console.print("[green]Parsing detailed netstat information...[/green]")
    connections = []
    try:
        netstat_output = execute_command(["netstat", "-anp", "tcp"])
        
        for line in netstat_output.splitlines():
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)\s+(\d+\.\d+\.\d+\.\d+)\.(\d+)\s+(\w+)', line)
            if match:
                local_ip = match.group(1)
                local_port = match.group(2)
                foreign_ip = match.group(3)
                foreign_port = match.group(4)
                state = match.group(5)
                
                connections.append({
                    "local_address": f"{local_ip}:{local_port}",
                    "foreign_address": f"{foreign_ip}:{foreign_port}",
                    "state": state,
                    "application": get_application_name(local_ip, local_port),
                    "country": get_country_from_ip(foreign_ip)
                })
        
        return connections
    except Exception as e:
        console.print(f"[red]Error parsing netstat details: {str(e)}[/red]")
        return []

def main():
    console.print("[bold blue]Starting comprehensive network monitoring...[/bold blue]")
    
    try:
        # Collect all network information
        network_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "network_info": get_system_network_info()
            },
            "open_ports": check_open_ports(),
            "active_connections": check_active_connections(),
            "detailed_connections": parse_netstat_details(),
            "bandwidth_usage": monitor_bandwidth_usage(),
            "dns_resolution": check_dns_resolution(),
            "ssl_certificates": check_ssl_certificates(),
            "network_performance": check_network_performance(),
            "wireless_info": check_wireless_info(),
            "firewall_status": check_firewall_status(),
            "network_devices": scan_network()
        }
        
        # Perform port scan on local IP
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 3389, 5900, 8080]
            network_data["port_scan"] = perform_port_scan(local_ip, common_ports)
        except Exception as e:
            console.print(f"[red]Error during port scan: {str(e)}[/red]")
            network_data["port_scan"] = {"error": str(e)}
        
        # Save to JSON file
        console.print(f"[yellow]Saving comprehensive report to: {NETWORK_REPORT}[/yellow]")
        with open(NETWORK_REPORT, 'w') as f:
            json.dump(network_data, f, indent=4)
        
        console.print("[bold green]Network monitoring complete![/bold green]")
        console.print(f"[blue]Detailed report saved to: {NETWORK_REPORT}[/blue]")
        
        # Print summary of findings
        console.print("\n[bold yellow]Summary of Network Analysis:[/bold yellow]")
        console.print(f"[cyan]System: {network_data['system_info']['system']} {network_data['system_info']['release']}[/cyan]")
        console.print(f"[cyan]Active Connections: {len(network_data['active_connections'])}[/cyan]")
        console.print(f"[cyan]Network Devices Found: {len(network_data['network_devices'])}[/cyan]")
        
        if isinstance(network_data['network_performance'], dict) and 'error' not in network_data['network_performance']:
            console.print(f"[cyan]Download Speed: {network_data['network_performance']['download_speed_mbps']} Mbps[/cyan]")
            console.print(f"[cyan]Upload Speed: {network_data['network_performance']['upload_speed_mbps']} Mbps[/cyan]")
            console.print(f"[cyan]Ping: {network_data['network_performance']['ping_ms']} ms[/cyan]")
        
    except Exception as e:
        console.print(f"[bold red]Error during monitoring: {str(e)}[/bold red]")
        raise

if __name__ == "__main__":
    main()