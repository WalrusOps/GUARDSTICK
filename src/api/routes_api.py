from flask import render_template, send_from_directory, jsonify

class RoutesAPI:
    """Handles all web page routes"""

    def __init__(self, app):
        self.app = app
        self.register_routes()

    def register_routes(self):
        """Register all web page routes"""

        # Home page route
        @self.app.route('/')
        def index():
            return render_template('index.html')

        # System Status page route
        @self.app.route('/system-status')
        def system_status_page():
            return render_template('system-status.html')

        # Security Tasks page route
        @self.app.route('/security-tasks')
        def security_tasks_page():
            return render_template('security-tasks.html')

        # Log Analysis page route
        @self.app.route('/log-analysis')
        def log_analysis_page():
            return render_template('log-analysis.html')

        # LLM Analysis page route
        @self.app.route('/llm-analysis')
        def llm_analysis_page():
            return render_template('llm-analysis.html')

        # Guide page route
        @self.app.route('/guide')
        def guide():
            return render_template('guide.html')

        # Static file serving for non-template files (e.g., JS, CSS)
        @self.app.route('/static/<path:path>')
        def serve_static(path):
            return send_from_directory(self.app.static_folder, path)

        # Security Events API endpoint
        @self.app.route('/api/security-events', methods=['GET'])
        def get_security_events():
            """Returns a list of security events"""
            # Example static data; replace with dynamic data fetching if needed
            events = [
                {"type": "Alert", "message": "Unauthorized login attempt detected", "timestamp": "2024-11-28T10:00:00Z"},
                {"type": "Warning", "message": "High CPU usage on server", "timestamp": "2024-11-28T10:05:00Z"}
            ]
            return jsonify({"status": "success", "events": events})

        # 404 Error Handling
        @self.app.errorhandler(404)
        def not_found_error(error):
            """Custom 404 error page"""
            try:
                return render_template('404.html'), 404
            except Exception:
                # Fallback in case the 404 template is missing
                return jsonify({"status": "error", "message": "Page not found"}), 404

        # Generic Error Handling
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            """Handle unexpected errors gracefully"""
            return jsonify({"status": "error", "message": str(e)}), 500