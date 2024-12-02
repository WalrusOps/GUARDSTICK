import os
import sys
import torch
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import secrets
import logging
import subprocess  # Required for health checks

# Dynamically identify the root directory of the project (GUARDSTICK)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the 'src' folder to sys.path to ensure proper module resolution
src_dir = os.path.join(PROJECT_ROOT)  # Absolute path to 'src'
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Add the static py folder to sys.path so that 'script_map' can be imported
static_py_dir = os.path.join(PROJECT_ROOT, 'app', 'static', 'py')
if static_py_dir not in sys.path:
    sys.path.insert(0, static_py_dir)

# Directories setup
STATIC_DIR = os.path.join(PROJECT_ROOT, 'app', 'static')
TEMPLATES_DIR = os.path.join(STATIC_DIR, 'templates')
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
REPORTS_DIR = os.path.join(DATA_DIR, 'log_reports')
EXPLOIT_DB_DIR = os.path.join(DATA_DIR, 'Exploit_DB')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')
CACHE_DIR = os.path.join(MODELS_DIR, 'cache')  # Cache directory for model downloads

# Ensure required directories exist
for directory in [REPORTS_DIR, EXPLOIT_DB_DIR, MODELS_DIR, CACHE_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logger Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask App Initialization
app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    template_folder=TEMPLATES_DIR
)

# Enable CORS with specific options
CORS(app)

app.secret_key = secrets.token_hex(16)
app.config['TEMPLATES_AUTO_RELOAD'] = True

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.disabled = True

# Import API modules after Flask app initialization
from api.routes_api import RoutesAPI
from api.system_api import SystemAPI
from api.logs_api import LogsAPI
from api.script_api import ScriptAPI
from api.llm_api import MistralLLMAPI, LLMConfig, LLMAPI

# Import script_map from static/py
from script_map import SCRIPT_MAP

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            "status": "error",
            "message": "Resource not found",
            "error": str(error)
        }), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal Server Error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error": str(error)
        }), 500
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions"""
    logger.error(f"Unhandled Exception: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred",
            "error": str(error)
        }), 500
    return render_template('500.html'), 500

# Health Indicators API
@app.route('/api/health-indicators', methods=['GET'])
def health_indicators():
    """Health Indicators API"""
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

    def get_firewall_status():
        try:
            result = subprocess.run(
                ["defaults", "read", "/Library/Preferences/com.apple.alf", "globalstate"],
                capture_output=True, text=True
            )
            status = int(result.stdout.strip())
            return "Active" if status == 1 else "Disabled"
        except Exception:
            return "Error"

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

    try:
        health_indicators = {
            "sip_status": get_sip_status(),
            "firewall_status": get_firewall_status(),
            "filevault_status": get_filevault_status(),
            "threat_level": "Low"  # Placeholder for dynamic threat level data
        }
        return jsonify({
            "status": "success",
            "health_indicators": health_indicators
        }), 200
    except Exception as e:
        logger.error(f"Error fetching health indicators: {e}")
        return jsonify({
            "status": "error",
            "message": "Unable to fetch health indicators"
        }), 500

# Initialize APIs
routes_api = RoutesAPI(app)
system_api = SystemAPI(app, logger)
logs_api = LogsAPI(app, logger, REPORTS_DIR)
script_api = ScriptAPI(app, logger, SCRIPTS_DIR, SCRIPT_MAP)

# Set environment variable for transformers cache
os.environ['TRANSFORMERS_CACHE'] = CACHE_DIR

# Initialize LLM with lazy initialization
llm_config = LLMConfig(
    model_name_or_path=os.path.join(PROJECT_ROOT, "models", "Mistral-7B-v0.3"),
    max_length=512,
    temperature=0.7,
    top_p=0.9,
    num_return_sequences=1,
    max_new_tokens=1024
)

llm_config.device = "cpu"  # Force CPU usage
mistral_llm = MistralLLMAPI(llm_config)
llm_api = LLMAPI(app, mistral_llm)

def initialize_llm():
    """Lazy initialization for LLM."""
    try:
        logger.info("Initializing Mistral-7B model...")
        if mistral_llm.initialize():
            logger.info(f"Mistral-7B initialized successfully on {mistral_llm.device}")
            logger.info(f"Using Metal Performance Shaders: {torch.backends.mps.is_available()}")
            return True
        else:
            logger.warning("Failed to initialize Mistral-7B - continuing without LLM functionality")
            return False
    except Exception as e:
        logger.error(f"Error initializing Mistral-7B: {str(e)}")
        logger.warning("Continuing without LLM functionality")
        return False

# Health check endpoint
@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print(f"Template folder: {TEMPLATES_DIR}")
    print(f"Static folder: {STATIC_DIR}")

    # Initialize LLM before starting the server
    llm_initialized = initialize_llm()
    if not llm_initialized:
        logger.warning("LLM functionality is unavailable; API will still serve non-LLM endpoints.")

    try:
        # Start Flask app with debug mode off
        app.run(host="0.0.0.0", port=5002, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}")
        sys.exit(1)
