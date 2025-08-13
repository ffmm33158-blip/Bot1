import os
import logging
from flask import Flask, jsonify, request
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def create_app(status_provider: Callable[[], dict], webhook_handler: Optional[Callable[[dict], None]] = None) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.get("/status")
    def status() -> tuple:
        try:
            data = status_provider() if status_provider else {}
            return jsonify({"status": "ok", "data": data}), 200
        except Exception:
            logger.exception("/status failed")
            return jsonify({"status": "error"}), 500

    if webhook_handler:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        path = f"/telegram/webhook/{token}" if token else "/telegram/webhook"

        @app.post(path)
        def telegram_webhook() -> tuple:
            try:
                payload = request.get_json(force=True, silent=True) or {}
                webhook_handler(payload)
                return "", 200
            except Exception:
                logger.exception("webhook error")
                return "", 200

    return app