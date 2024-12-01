from flask import jsonify, request, send_from_directory
import os
import json  # Add JSON import to handle JSON log files
from datetime import datetime

class LogsAPI:
    """Handles log-related endpoints"""
    
    def __init__(self, app, logger, reports_dir):
        self.app = app
        self.logger = logger
        self.reports_dir = reports_dir
        self.register_routes()

    def register_routes(self):
        @self.app.route("/api/get-logs", methods=["GET"])
        def get_logs():
            """Fetch logs with timestamps."""
            log_files = []
            try:
                # Ensure reports directory exists
                if not os.path.exists(self.reports_dir):
                    self.logger.warning(f"Reports directory does not exist: {self.reports_dir}")
                    return jsonify({"status": "error", "message": "Reports directory not found"}), 404

                # Gather log files (for both .txt and .json)
                for file in os.listdir(self.reports_dir):
                    if file.endswith(('.txt', '.json')):  # Fetch both .txt and .json files
                        file_path = os.path.join(self.reports_dir, file)
                        file_size = os.path.getsize(file_path)
                        file_timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()  # Get last modified time
                        log_files.append({
                            "name": file,
                            "size": f"{file_size / 1024:.1f} KB" if file_size > 1024 else f"{file_size} bytes",
                            "timestamp": file_timestamp,
                            "download_url": f"/api/logs/download/{file}"
                        })

                if not log_files:
                    self.logger.info(f"No log files found in {self.reports_dir}")
                    return jsonify({"status": "success", "logs": []}), 200

                self.logger.info(f"Retrieved {len(log_files)} log file(s)")
                return jsonify({"status": "success", "logs": log_files}), 200

            except Exception as e:
                self.logger.error(f"Error fetching logs: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/api/logs/download/<filename>", methods=["GET"])
        def download_log(filename):
            """Downloads a specified log file."""
            try:
                file_path = os.path.join(self.reports_dir, filename)
                if not os.path.exists(file_path):
                    self.logger.warning(f"Log file not found: {file_path}")
                    return jsonify({"status": "error", "message": "Log file not found"}), 404
                self.logger.info(f"Downloading log file: {filename}")
                return send_from_directory(self.reports_dir, filename, as_attachment=True)
            except Exception as e:
                self.logger.error(f"Error downloading log file {filename}: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/api/logs/delete", methods=["POST"])
        def delete_logs():
            """Deletes selected log files."""
            try:
                data = request.json
                selected_logs = data.get('logs', [])
                if not selected_logs:
                    self.logger.warning("No logs selected for deletion")
                    return jsonify({"status": "error", "message": "No logs selected for deletion"}), 400

                deleted_logs = []
                for log_name in selected_logs:
                    file_path = os.path.join(self.reports_dir, log_name)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_logs.append(log_name)
                        self.logger.info(f"Deleted log file: {log_name}")
                    else:
                        self.logger.warning(f"Log file not found for deletion: {log_name}")

                if not deleted_logs:
                    return jsonify({"status": "error", "message": "No valid logs found for deletion"}), 400

                self.logger.info(f"Deleted {len(deleted_logs)} log file(s)")
                return jsonify({
                    "status": "success",
                    "message": f"Deleted {len(deleted_logs)} log(s)",
                    "deleted_logs": deleted_logs
                }), 200
            except Exception as e:
                self.logger.error(f"Error deleting logs: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
