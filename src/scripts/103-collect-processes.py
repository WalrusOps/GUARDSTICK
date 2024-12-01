import os
import subprocess
import json

# Define directories and report file
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))  # Root directory
SRC_DIR = os.path.join(ROOT_DIR, "src")                                        # Source directory
DATA_DIR = os.path.join(SRC_DIR, "data")                                       # Data directory
REPORTS_DIR = os.path.join(DATA_DIR, "log_reports")                            # Log reports directory
os.makedirs(REPORTS_DIR, exist_ok=True)
PROCESS_FILE = os.path.join(REPORTS_DIR, "Running_Processes.json")

def collect_running_processes():
    """Collect and save relevant running processes to a JSON file."""
    processes = []

    # Execute `ps aux` to get the list of running processes
    result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    process_data = result.stdout.splitlines()

    # Define keywords for relevant applications
    relevant_keywords = ["chrome", "safari", "firefox", "spotify", "code", "mail", "slack", "zoom", "teams", "brave"]

    # Parse the output of `ps aux`
    for line in process_data[1:]:  # Skip the header
        parts = line.split(maxsplit=10)
        if len(parts) >= 11:
            user = parts[0]
            pid = parts[1]
            cpu = parts[2]
            mem = parts[3]
            command = parts[10]

            # Check if the command contains any of the relevant keywords
            if any(keyword in command.lower() for keyword in relevant_keywords):
                # Filter out command-line arguments starting with "--"
                main_command = ' '.join([part for part in command.split() if not part.startswith("--")])

                # Extract the application name from the main command
                process_name = main_command.split('/')[-1] if '/' in main_command else main_command
                # Shorten lengthy commands for readability
                if len(main_command) > 35:
                    main_command = main_command[:32] + "..."

                # Append the process data
                processes.append({
                    "name": process_name,
                    "user": user,
                    "pid": pid,
                    "cpu": cpu,
                    "mem": mem,
                    "command": main_command
                })

    # Save the collected data to a JSON file
    with open(PROCESS_FILE, "w") as f:
        json.dump(processes, f, indent=4)

def main():
    collect_running_processes()

if __name__ == "__main__":
    main()