# src/api/script_api.py

from flask import jsonify, request
import os
import subprocess
import logging
from datetime import datetime

class ScriptAPI:
    """Handles security script execution and management"""
    
    def __init__(self, app, logger, scripts_dir, script_map):
        self.app = app
        self.logger = logger
        self.scripts_dir = scripts_dir
        self.script_map = script_map
        self.register_routes()

    def register_routes(self):
        @self.app.route("/api/execute", methods=["POST"])
        def execute_script():
            try:
                data = request.json
                if not data or 'script' not in data:
                    return jsonify({
                        "status": "error",
                        "message": "No script specified"
                    }), 400

                script_key = data['script']
                if script_key not in self.script_map:
                    return jsonify({
                        "status": "error",
                        "message": f"Invalid script key: {script_key}"
                    }), 400

                script_filename, output_filename = self.script_map[script_key]
                script_path = os.path.join(self.scripts_dir, script_filename)

                if not os.path.exists(script_path):
                    return jsonify({
                        "status": "error",
                        "message": f"Script file not found: {script_filename}"
                    }), 404

                # Execute the script
                result = self.execute_python_script(script_path)
                
                return jsonify({
                    "status": "success",
                    "output": result,
                    "script": script_key,
                    "timestamp": datetime.now().isoformat()
                }), 200

            except Exception as e:
                self.logger.error(f"Error executing script: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500

    def execute_python_script(self, script_path):
        """
        Execute a Python script and return its output
        """
        try:
            # Using subprocess to run the script
            result = subprocess.run(
                ['python3', script_path],
                capture_output=True,
                text=True,
                timeout=1800  # 5 minute timeout
            )

            # Log the execution
            self.logger.info(f"Executed script: {script_path}")
            if result.stderr:
                self.logger.warning(f"Script stderr: {result.stderr}")

            # Return combined output
            output = result.stdout
            if result.stderr:
                output += f"\nErrors/Warnings:\n{result.stderr}"
            
            return output

        except subprocess.TimeoutExpired:
            error_msg = f"Script execution timed out: {script_path}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Error executing script {script_path}: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def get_script_status(self, script_key):
        """
        Get the status of a script (whether it exists and is executable)
        """
        try:
            if script_key not in self.script_map:
                return {
                    "status": "error",
                    "message": f"Invalid script key: {script_key}"
                }

            script_filename, _ = self.script_map[script_key]
            script_path = os.path.join(self.scripts_dir, script_filename)

            if not os.path.exists(script_path):
                return {
                    "status": "error",
                    "message": "Script file not found"
                }

            return {
                "status": "available",
                "path": script_path,
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(script_path)
                ).isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error checking script status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_available_scripts(self):
        """
        Get a list of all available scripts and their status
        """
        available_scripts = {}
        for key, (script_filename, output_filename) in self.script_map.items():
            script_path = os.path.join(self.scripts_dir, script_filename)
            available_scripts[key] = {
                "filename": script_filename,
                "output_file": output_filename,
                "exists": os.path.exists(script_path),
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(script_path)
                ).isoformat() if os.path.exists(script_path) else None
            }
        return available_scripts