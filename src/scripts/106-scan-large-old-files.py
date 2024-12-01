import os
from datetime import datetime

# Define report paths
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/data/log_reports"))
FILES_LOG = os.path.join(REPORTS_DIR, "Large_Old_Files.txt")

# Ensure the report directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

# Function to log results to file
def log_results(header, content):
    """Log scan results with a specific header."""
    with open(FILES_LOG, "a") as f:
        f.write(f"{header}\n{'=' * 50}\n{content}\n\n")

# Function to scan for large files
def scan_large_files():
    """Scan for files larger than 500MB in specific directories."""
    directories = ["/Users", "/Applications", "/Library"]
    large_files = []

    for dir_path in directories:
        result = os.popen(f"find {dir_path} -type f -size +500M -exec ls -lh {{}} + 2>/dev/null").read()
        if result.strip():
            large_files.append(f"Directory: {dir_path}\n{result.strip()}")

    log_results("Large Files (500MB+)", "\n\n".join(large_files) if large_files else "No large files found.")

# Function to scan for old files
def scan_old_files():
    """Scan for files older than 180 days in specific directories."""
    directories = ["/Users", "/Applications", "/Library"]
    old_files = []

    for dir_path in directories:
        result = os.popen(f"find {dir_path} -type f -mtime +180 -exec ls -lh {{}} + 2>/dev/null").read()
        if result.strip():
            old_files.append(f"Directory: {dir_path}\n{result.strip()}")

    log_results("Old Files (older than 180 days)", "\n\n".join(old_files) if old_files else "No old files found.")

# Main execution
def main():
    # Initialize the log file with a header
    with open(FILES_LOG, "w") as f:
        f.write(f"Large and Old Files Report - Generated on {datetime.now()}\n{'=' * 50}\n\n")

    # Perform scans
    scan_large_files()
    scan_old_files()

if __name__ == "__main__":
    main()