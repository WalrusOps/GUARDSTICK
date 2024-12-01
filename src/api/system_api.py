from flask import jsonify
import psutil
import platform
from datetime import datetime

class SystemAPI:
    def __init__(self, app, logger):
        self.app = app
        self.logger = logger
        self.register_routes()

    def register_routes(self):
        @self.app.route("/api/system-status", methods=["GET"])
        def get_system_status():
            try:
                # Get real CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Get real memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Get real disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # Get real system uptime
                boot_time = psutil.boot_time()
                uptime = datetime.now().timestamp() - boot_time
                days, remainder = divmod(int(uptime), 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

                status = {
                    "cpu_usage": f"{cpu_percent}%",
                    "memory_usage": f"{memory_percent}%",
                    "disk_usage": f"{disk_percent}%",
                    "uptime": uptime_str,
                    "detailed_memory": {
                        "total": f"{memory.total / (1024**3):.2f} GB",
                        "available": f"{memory.available / (1024**3):.2f} GB",
                        "used": f"{(memory.total - memory.available) / (1024**3):.2f} GB"
                    },
                    "detailed_disk": {
                        "total": f"{disk.total / (1024**3):.2f} GB",
                        "used": f"{disk.used / (1024**3):.2f} GB",
                        "free": f"{disk.free / (1024**3):.2f} GB"
                    }
                }
                
                return jsonify({"status": "success", "system_info": status}), 200
            except Exception as e:
                self.logger.error(f"Error fetching system status: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500