from flask import Flask, jsonify
from typing import Dict, Any, Callable

def create_app(status_provider: Callable[[], Dict[str, Any]] = None) -> Flask:
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})
    
    @app.route('/status')
    def status():
        if status_provider:
            try:
                data = status_provider()
                return jsonify(data)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        return jsonify({"message": "Status provider not configured"})
    
    return app
