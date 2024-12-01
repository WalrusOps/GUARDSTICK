from flask import jsonify
import subprocess

# Helper Function: SIP Status
def get_sip_status():
    try:
        result = subprocess.run(["csrutil", "status"], capture_output=True, text=True)
        if "enabled" in result.stdout.lower():
            return "Enabled"
        elif "disabled" in result.stdout.lower():
            return "Disabled"
        return "Unknown"
    except Exception:
        return "Error"

# Helper Function: Firewall Status
def get_firewall_status():
    try:
        result = subprocess.run(
            ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            if "enabled" in result.stdout.lower():
                return "Enabled"
            elif "disabled" in result.stdout.lower():
                return "Disabled"
        return "Unknown"
    except Exception:
        return "Error"

# Helper Function: FileVault Status
def get_filevault_status():
    try:
        result = subprocess.run(["fdesetup", "status"], capture_output=True, text=True)
        if "on" in result.stdout.lower():
            return "Enabled"
        elif "off" in result.stdout.lower():
            return "Disabled"
        return "Unknown"
    except Exception:
        return "Error"

# Helper Function: Active Network Interfaces (9)
def get_active_network_interfaces():
    try:
        result = subprocess.run(["ifconfig"], capture_output=True, text=True)
        if result.returncode == 0:
            active_interfaces = [
                line.split(":")[0] for line in result.stdout.splitlines() if "status: active" in line
            ]
            return ", ".join(active_interfaces) if active_interfaces else "None"
        return "Error"
    except Exception:
        return "Error"

# Helper Function: App Quarantine Status (10)
def get_app_quarantine_status():
    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.LaunchServices", "LSQuarantine"],
            capture_output=True,
            text=True
        )
        if "1" in result.stdout.strip():
            return "Enabled"
        elif "0" in result.stdout.strip():
            return "Disabled"
        return "Unknown"
    except Exception:
        return "Error"

# Helper Function: Battery Health (11)
def get_battery_health():
    try:
        result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            if "InternalBattery" in lines[0]:
                return lines[0].split(";")[1].strip()  # Extract the battery percentage and status
            return "No Battery"
        return "Error"
    except Exception:
        return "Error"

# Helper Function: Gatekeeper Status (7)
def get_gatekeeper_status():
    try:
        result = subprocess.run(["spctl", "--status"], capture_output=True, text=True)
        if "assessments enabled" in result.stdout.lower():
            return "Enabled"
        elif "assessments disabled" in result.stdout.lower():
            return "Disabled"
        return "Unknown"
    except Exception:
        return "Error"

# Helper Function: Antivirus Status (1)
def get_antivirus_status():
    try:
        result = subprocess.run(
            ["system_profiler", "SPInstallHistoryDataType"],
            capture_output=True,
            text=True
        )
        if "antivirus" in result.stdout.lower():
            return "Installed"
        return "Not Installed"
    except Exception:
        return "Error"

# Register Health API
def register_health_api(app):
    @app.route('/api/health-indicators', methods=['GET'])
    def get_health_indicators():
        try:
            health_indicators = {
                "sip_status": get_sip_status(),
                "firewall_status": get_firewall_status(),
                "filevault_status": get_filevault_status(),
                "active_network_interfaces": get_active_network_interfaces(),
                "app_quarantine_status": get_app_quarantine_status(),
                "battery_health": get_battery_health(),
                "gatekeeper_status": get_gatekeeper_status(),
                "antivirus_status": get_antivirus_status(),
                "threat_level": "Low"  # Placeholder for additional checks
            }
            return jsonify({
                "status": "success",
                "health_indicators": health_indicators
            }), 200
        except Exception as e:
            app.logger.error(f"Error fetching health indicators: {e}")
            return jsonify({
                "status": "error",
                "message": "Unable to fetch health indicators"
            }), 500
