import os
import json
import subprocess
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

# Set up base directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DATA_DIR = os.path.join(SRC_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Initialize console
console = Console()

def generate_report_filename(scan_type):
    """Generate a timestamped JSON filename."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{scan_type}_Report_{timestamp}.json"

def save_json(data, scan_type):
    """Save data to a JSON file."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return report_file

def explain_process():
    """Display the purpose of the script using a styled panel."""
    console.print(Panel.fit(
        "[bold cyan]🔍 Scanning for Installed Browser Extensions[/bold cyan]\n\n"
        "This script scans installed browser extensions for potential security risks.\n\n"
        "Browsers included:\n"
        " - Google Chrome\n"
        " - Brave\n"
        " - Safari\n"
        " - Firefox\n",
        border_style="cyan"))

def scan_chrome_brave_extensions(browser_name, browser_dir):
    """Scan Chrome and Brave extensions and log results."""
    extensions = []
    extensions_dir = os.path.join(browser_dir, "Default", "Extensions")
    if os.path.isdir(extensions_dir):
        for ext_id in track(os.listdir(extensions_dir), description=f"Scanning {browser_name} extensions..."):
            ext_path = os.path.join(extensions_dir, ext_id)
            if os.path.isdir(ext_path):
                version_dirs = os.listdir(ext_path)
                if version_dirs:
                    manifest_path = os.path.join(ext_path, version_dirs[0], "manifest.json")
                    ext_name = get_extension_name_from_manifest(manifest_path)
                    extensions.append({
                        "extension_id": ext_id,
                        "name": ext_name or "Name not found",
                        "browser": browser_name
                    })
    return extensions

def scan_safari_extensions():
    """Scan Safari extensions."""
    extensions = []
    safari_plist = os.path.expanduser("~/Library/Containers/com.apple.Safari/Data/Library/Preferences/com.apple.Safari.plist")
    if os.path.exists(safari_plist):
        safari_output = subprocess.run(
            ["/usr/libexec/PlistBuddy", "-c", "Print :ManagedExtensions", safari_plist],
            capture_output=True, text=True
        )
        if safari_output.stdout.strip():
            extensions.append({
                "name": safari_output.stdout.strip(),
                "browser": "Safari"
            })
    return extensions

def scan_firefox_extensions():
    """Scan Firefox extensions."""
    extensions = []
    firefox_dir = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
    if os.path.isdir(firefox_dir):
        for profile in os.listdir(firefox_dir):
            profile_path = os.path.join(firefox_dir, profile)
            if os.path.isdir(profile_path):
                extensions_json_path = os.path.join(profile_path, "extensions.json")
                if os.path.exists(extensions_json_path):
                    try:
                        with open(extensions_json_path, 'r') as f:
                            data = json.load(f)
                            addons = data.get('addons', [])
                            for addon in addons:
                                if addon.get('type') == 'extension':
                                    extensions.append({
                                        "name": addon.get('name', 'Unknown'),
                                        "browser": "Firefox",
                                        "profile": profile
                                    })
                    except json.JSONDecodeError:
                        pass
    return extensions

def get_extension_name_from_manifest(manifest_path):
    """Extract the name from manifest.json or resolve localized names."""
    if not os.path.exists(manifest_path):
        return "Unknown"

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            name = manifest.get('name')

            # Resolve localized name if applicable
            if name and name.startswith('__MSG_'):
                name_key = name[6:-2]
                locales_dir = os.path.join(os.path.dirname(manifest_path), "_locales")
                return resolve_localized_name(locales_dir, name_key) or "Unknown Localized Name"
            return name or "Unknown"
    except json.JSONDecodeError:
        return "Malformed manifest"

def resolve_localized_name(locales_dir, name_key):
    """Resolve a localized name for the extension."""
    if not os.path.isdir(locales_dir):
        return None

    for locale in os.listdir(locales_dir):
        messages_file = os.path.join(locales_dir, locale, "messages.json")
        if os.path.isfile(messages_file):
            try:
                with open(messages_file, 'r') as f:
                    messages = json.load(f)
                    if name_key in messages:
                        return messages[name_key].get('message')
            except json.JSONDecodeError:
                continue
    return None

def scan_safari_extensions():
    """Scan Safari extensions and filter out invalid results."""
    extensions = []
    safari_plist = os.path.expanduser("~/Library/Containers/com.apple.Safari/Data/Library/Preferences/com.apple.Safari.plist")
    if os.path.exists(safari_plist):
        safari_output = subprocess.run(
            ["/usr/libexec/PlistBuddy", "-c", "Print :ManagedExtensions", safari_plist],
            capture_output=True, text=True
        )
        if safari_output.stdout.strip():
            extensions.append({
                "name": safari_output.stdout.strip(),
                "browser": "Safari"
            })
    return extensions

def scan_firefox_extensions():
    """Scan Firefox extensions with better error handling."""
    extensions = []
    firefox_dir = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
    if os.path.isdir(firefox_dir):
        for profile in os.listdir(firefox_dir):
            profile_path = os.path.join(firefox_dir, profile)
            if os.path.isdir(profile_path):
                extensions_json_path = os.path.join(profile_path, "extensions.json")
                if os.path.exists(extensions_json_path):
                    try:
                        with open(extensions_json_path, 'r') as f:
                            data = json.load(f)
                            addons = data.get('addons', [])
                            for addon in addons:
                                if addon.get('type') == 'extension':
                                    extensions.append({
                                        "name": addon.get('name', 'Unknown'),
                                        "browser": "Firefox",
                                        "profile": profile
                                    })
                    except json.JSONDecodeError:
                        extensions.append({
                            "name": "Error reading extensions.json",
                            "browser": "Firefox",
                            "profile": profile
                        })
    return extensions

def main():
    explain_process()

    all_extensions = {
        "scan_metadata": {
            "scan_name": "Browser Extensions Report",
            "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tool_name": "Browser Extension Scanner"
        },
        "results": []
    }

    all_extensions["results"].extend(scan_chrome_brave_extensions("Google Chrome", os.path.expanduser("~/Library/Application Support/Google/Chrome")))
    all_extensions["results"].extend(scan_chrome_brave_extensions("Brave", os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser")))
    all_extensions["results"].extend(scan_safari_extensions())
    all_extensions["results"].extend(scan_firefox_extensions())

    report_file = save_json(all_extensions, "Browser_Extensions")
    console.print(f"\n[bold green]Browser extensions scan completed.[/bold green]")
    console.print(f"[bold green]A report of this scan has been saved at {report_file}[/bold green]")

if __name__ == "__main__":
    main()