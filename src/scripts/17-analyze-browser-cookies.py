import os
import sqlite3
import json
import shutil
import tempfile
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm
from datetime import datetime
from collections import defaultdict

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
    """Save data to a JSON file."""
    report_file = os.path.join(REPORTS_DIR, generate_report_filename(scan_type))
    with open(report_file, 'w') as f:
        json.dump(data, f, indent=4)
    return report_file

console = Console()

# Risk categories for cookies and domains
HIGH_RISK_KEYWORDS = {
    'auth': 'Authentication token',
    'session': 'Session identifier',
    'login': 'Login credentials',
    'token': 'Access token',
    'admin': 'Administrative access',
    'jwt': 'JSON Web Token',
    'pass': 'Password related',
    'secure': 'Security related',
    'access': 'Access control',
    'oauth': 'OAuth token'
}

class BrowserAnalyzer:
    def __init__(self):
        self.browsers = {
            "Chrome": {
                "cookies_path": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
                "passwords_path": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Login Data"),
                "cookie_query": """
                    SELECT host_key, name, path, datetime(creation_utc, 'unixepoch') as created,
                    datetime(last_access_utc, 'unixepoch') as last_accessed,
                    is_secure, is_httponly, value
                    FROM cookies
                """,
                "password_query": """
                    SELECT origin_url, username_value, 
                    datetime(date_created, 'unixepoch') as created,
                    datetime(date_last_used, 'unixepoch') as last_used,
                    times_used
                    FROM logins ORDER BY times_used DESC
                """
            },
            "Firefox": {
                "cookies_path": os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*.default-release/cookies.sqlite"),
                "passwords_path": os.path.expanduser("~/Library/Application Support/Firefox/Profiles/*.default-release/logins.json"),
                "cookie_query": """
                    SELECT host, name, path, datetime(creationTime/1000000, 'unixepoch') as created,
                    datetime(lastAccessed/1000000, 'unixepoch') as last_accessed,
                    isSecure, isHttpOnly, value
                    FROM moz_cookies
                """
            },
            "Brave": {
                "cookies_path": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies"),
                "passwords_path": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Login Data"),
                "cookie_query": """
                    SELECT host_key, name, path, datetime(creation_utc, 'unixepoch') as created,
                    datetime(last_access_utc, 'unixepoch') as last_accessed,
                    is_secure, is_httponly, value
                    FROM cookies
                """,
                "password_query": """
                    SELECT origin_url, username_value,
                    datetime(date_created, 'unixepoch') as created,
                    datetime(date_last_used, 'unixepoch') as last_used,
                    times_used
                    FROM logins ORDER BY times_used DESC
                """
            }
        }

    def analyze_cookies(self, browser_name, browser_info):
        """Analyze cookies for a specific browser."""
        results = {
            "count": 0,
            "secure_count": 0,
            "httponly_count": 0,
            "domains": defaultdict(int),
            "high_risk": [],
            "recent_cookies": [],
            "statistics": defaultdict(int)
        }

        try:
            if not os.path.exists(browser_info["cookies_path"]):
                return results

            temp_db = tempfile.NamedTemporaryFile(delete=False).name
            shutil.copy2(browser_info["cookies_path"], temp_db)

            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute(browser_info["cookie_query"])
                cookies = cursor.fetchall()

                for cookie in cookies:
                    results["count"] += 1
                    host = cookie[0]
                    name = cookie[1]
                    created = cookie[3]
                    last_accessed = cookie[4]
                    is_secure = cookie[5]
                    is_httponly = cookie[6]

                    results["domains"][host] += 1
                    if is_secure:
                        results["secure_count"] += 1
                    if is_httponly:
                        results["httponly_count"] += 1

                    cookie_lower = name.lower()
                    for keyword, risk_type in HIGH_RISK_KEYWORDS.items():
                        if keyword in cookie_lower:
                            results["high_risk"].append({
                                "domain": host,
                                "name": name,
                                "type": risk_type,
                                "secure": bool(is_secure),
                                "httponly": bool(is_httponly),
                                "last_accessed": last_accessed
                            })
                            break

                    if last_accessed:
                        try:
                            access_date = datetime.strptime(last_accessed, '%Y-%m-%d %H:%M:%S')
                            if (datetime.now() - access_date).days <= 7:
                                results["recent_cookies"].append({
                                    "domain": host,
                                    "name": name,
                                    "last_accessed": last_accessed
                                })
                        except ValueError:
                            pass

            os.unlink(temp_db)

            results["statistics"] = {
                "total_domains": len(results["domains"]),
                "avg_cookies_per_domain": round(results["count"] / len(results["domains"]) if results["domains"] else 0, 2),
                "high_risk_count": len(results["high_risk"]),
                "recent_count": len(results["recent_cookies"])
            }

        except Exception as e:
            console.print(f"[red]Error analyzing {browser_name} cookies: {str(e)}[/red]")

        return results

    def analyze_passwords(self, browser_name, browser_info):
        """Analyze stored passwords for a specific browser."""
        results = {
            "count": 0,
            "domains": defaultdict(int),
            "statistics": {}
        }

        try:
            if not os.path.exists(browser_info["passwords_path"]):
                return results

            temp_db = tempfile.NamedTemporaryFile(delete=False).name
            shutil.copy2(browser_info["passwords_path"], temp_db)

            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute(browser_info["password_query"])
                passwords = cursor.fetchall()

                for password in passwords:
                    url = password[0]
                    username = password[1]
                    results["count"] += 1
                    results["domains"][url] += 1

            os.unlink(temp_db)

            results["statistics"] = {
                "total_domains": len(results["domains"]),
            }

        except Exception as e:
            console.print(f"[red]Error analyzing {browser_name} passwords: {str(e)}[/red]")

        return results

def main():
    analyzer = BrowserAnalyzer()
    analysis_results = {}

    with Progress() as progress:
        scan_task = progress.add_task("Analyzing browsers...", total=len(analyzer.browsers) * 2)

        for browser_name, browser_info in analyzer.browsers.items():
            analysis_results[browser_name] = {
                "cookies": analyzer.analyze_cookies(browser_name, browser_info),
                "passwords": analyzer.analyze_passwords(browser_name, browser_info),
            }
            progress.update(scan_task, advance=2)

    report_file = save_json(analysis_results, "Browser_Security")
    console.print(f"[green]Analysis complete. Report saved to: [bold magenta]{report_file}[/bold magenta][/green]")

if __name__ == "__main__":
    main()