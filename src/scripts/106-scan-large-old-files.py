import os
import json
import hashlib
from datetime import datetime
from collections import defaultdict
import shutil

# Define report paths
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/data/log_reports"))
SCAN_REPORT = os.path.join(REPORTS_DIR, f"file_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

# Ensure the report directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_file_hash(filepath, block_size=65536):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha256_hash.update(block)
        return sha256_hash.hexdigest()
    except (PermissionError, FileNotFoundError):
        return None

def get_file_extension(filepath):
    """Get the file extension in lowercase."""
    return os.path.splitext(filepath)[1].lower()

def get_disk_usage(directory):
    """Get disk usage statistics for a directory."""
    try:
        total, used, free = shutil.disk_usage(directory)
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percentage": round((used / total) * 100, 2)
        }
    except:
        return None

def find_duplicate_files(files_list):
    """Find duplicate files based on size and hash."""
    size_groups = defaultdict(list)
    for file_info in files_list:
        size_groups[file_info["size_bytes"]].append(file_info)
    
    duplicates = []
    for size, files in size_groups.items():
        if len(files) > 1:
            hash_groups = defaultdict(list)
            for file_info in files:
                file_hash = get_file_hash(file_info["path"])
                if file_hash:
                    hash_groups[file_hash].append(file_info)
            
            for hash_group in hash_groups.values():
                if len(hash_group) > 1:
                    duplicates.append(hash_group)
    
    return duplicates

def get_file_info(filepath):
    """Get file information in a structured format."""
    stats = os.stat(filepath)
    size_bytes = stats.st_size
    size_mb = size_bytes / (1024 * 1024)  # Convert to MB for readable size
    
    return {
        "path": filepath,
        "filename": os.path.basename(filepath),
        "extension": get_file_extension(filepath),
        "size_bytes": size_bytes,
        "size_readable": f"{size_mb:.2f} MB",
        "created_time": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "last_accessed": datetime.fromtimestamp(stats.st_atime).isoformat(),
        "days_old": (datetime.now() - datetime.fromtimestamp(stats.st_mtime)).days,
        "permissions": oct(stats.st_mode)[-3:],
        "owner": stats.st_uid,
        "group": stats.st_gid,
        "hash": get_file_hash(filepath)
    }

def scan_directory(directory, min_size_mb=500, min_age_days=180):
    """Scan directory for file analysis."""
    results = {
        "scan_info": {
            "directory": directory,
            "scan_time": datetime.now().isoformat(),
            "disk_usage": get_disk_usage(directory)
        },
        "large_files": [],
        "old_files": [],
        "extensions": defaultdict(int),
        "size_distribution": {
            "0-1MB": 0,
            "1-10MB": 0,
            "10-100MB": 0,
            "100MB-1GB": 0,
            "1GB+": 0
        }
    }
    
    all_files = []  # Keep track of all files for duplicate detection
    
    try:
        # Scan only the immediate directory, not subdirectories
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            # Skip if not a file or if hidden
            if not os.path.isfile(filepath) or filename.startswith('.'):
                continue
                
            file_info = get_file_info(filepath)
            all_files.append(file_info)
            
            # Update extension statistics
            results["extensions"][file_info["extension"]] += 1
            
            # Update size distribution
            size_mb = file_info["size_bytes"] / (1024 * 1024)
            if size_mb < 1:
                results["size_distribution"]["0-1MB"] += 1
            elif size_mb < 10:
                results["size_distribution"]["1-10MB"] += 1
            elif size_mb < 100:
                results["size_distribution"]["10-100MB"] += 1
            elif size_mb < 1024:
                results["size_distribution"]["100MB-1GB"] += 1
            else:
                results["size_distribution"]["1GB+"] += 1
            
            # Check size and age criteria
            if size_mb >= min_size_mb:
                results["large_files"].append(file_info)
            if file_info["days_old"] >= min_age_days:
                results["old_files"].append(file_info)
    
    except (PermissionError, FileNotFoundError) as e:
        results["scan_info"]["error"] = str(e)
    
    # Find duplicates
    results["duplicate_files"] = find_duplicate_files(all_files)
    
    # Convert defaultdict to regular dict for JSON serialization
    results["extensions"] = dict(results["extensions"])
    
    return results

def main():
    """Main execution function."""
    scan_results = {
        "scan_time": datetime.now().isoformat(),
        "system_info": {
            "total_disk_usage": get_disk_usage("/")
        },
        "user_directories": {}
    }
    
    # Scan each user's home directory
    for user_dir in [d for d in os.listdir('/Users') 
                    if os.path.isdir(os.path.join('/Users', d)) 
                    and not d.startswith('.') 
                    and not d == 'Shared']:
        user_path = os.path.join('/Users', user_dir)
        scan_results["user_directories"][user_dir] = scan_directory(user_path)
    
    # Write results to JSON file
    with open(SCAN_REPORT, 'w') as f:
        json.dump(scan_results, f, indent=4)
    
    print(f"Scan completed. Results written to {SCAN_REPORT}")

if __name__ == "__main__":
    main()