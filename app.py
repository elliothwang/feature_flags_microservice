import os
from flask import Flask, jsonify, request

# simple in-memory feature flag store
# you can extend this with more flags later
FLAGS = {}

ALLOWED_MODES = {"test", "production"}
ENVIRONMENT_FLAG_NAME = "environment_mode"


def _get_default_mode() -> str:
    """
    reads the default environment mode from env or falls back to test
    """
    env_mode = os.environ.get("FEATURE_FLAG_DEFAULT_MODE", "test").lower()
    if env_mode in ALLOWED_MODES:
        return env_mode
    return "test"


def _initialize_flags() -> None:
    """
    sets up initial flags when the service starts
    """
    default_mode = _get_default_mode()
    FLAGS[ENVIRONMENT_FLAG_NAME] = default_mode


_initialize_flags()

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False  # keep responses in a predictable order


# -----------------------------
# health
# -----------------------------


@app.route("/health", methods=["GET"])
def health():
    """
    health check endpoint
    """
    return jsonify(
        {
            "status": "ok",
            "service": "feature-flag",
            "mode": FLAGS.get(ENVIRONMENT_FLAG_NAME, "test"),
        }
    ), 200


# -----------------------------
# generic flags endpoints
# -----------------------------


@app.route("/flags", methods=["GET"])
def get_all_flags():
    """
    returns all current feature flags
    """
    return jsonify(
        {
            "status": "ok",
            "flags": FLAGS,
        }
    ), 200


@app.route("/flags/<name>", methods=["GET"])
def get_single_flag(name: str):
    """
    returns a single feature flag by name
    """
    if name not in FLAGS:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"flag '{name}' not found",
                }
            ),
            404,
        )

    return (
        jsonify(
            {
                "status": "ok",
                "name": name,
                "value": FLAGS[name],
            }
        ),
        200,
    )


@app.route("/flags", methods=["POST"])
def create_or_update_flag():
    """
    creates or updates a feature flag
    expects JSON body: { "name": <str>, "value": <any> }
    """
    if not request.is_json:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "expected JSON body with 'name' and 'value' fields",
                }
            ),
            400,
        )

    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    value = payload.get("value", None)

    # basic validation
    if not name:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "flag 'name' must be a non-empty string",
                }
            ),
            400,
        )

    if value is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "flag 'value' must be provided",
                }
            ),
            400,
        )

    # special rules for environment_mode
    if name == ENVIRONMENT_FLAG_NAME:
        mode_str = str(value).lower()
        if mode_str not in ALLOWED_MODES:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "invalid mode; environment_mode must be 'test' or 'production'",
                    }
                ),
                400,
            )
        value = mode_str

    FLAGS[name] = value

    return (
        jsonify(
            {
                "status": "ok",
                "name": name,
                "value": value,
            }
        ),
        200,
    )


# -----------------------------
# convenience mode endpoints
# -----------------------------


@app.route("/mode", methods=["GET"])
def get_mode():
    """
    returns the current environment mode (wrapper around environment_mode flag)
    """
    mode = FLAGS.get(ENVIRONMENT_FLAG_NAME, "test")
    return jsonify({"status": "ok", "mode": mode}), 200


@app.route("/mode", methods=["POST"])
def set_mode():
    """
    updates the environment mode between test and production
    expects JSON body: { "mode": "test" | "production" }
    """
    if not request.is_json:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "expected JSON body with a 'mode' field",
                }
            ),
            400,
        )

    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "")).lower().strip()

    if mode not in ALLOWED_MODES:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "invalid mode; must be 'test' or 'production'",
                }
            ),
            400,
        )

    FLAGS[ENVIRONMENT_FLAG_NAME] = mode

    return jsonify({"status": "ok", "mode": mode}), 200


# -----------------------------
# errors and app factory
# -----------------------------


@app.errorhandler(404)
def not_found(_error):
    """
    simple 404 handler for unknown routes
    """
    return (
        jsonify(
            {
                "status": "error",
                "message": "endpoint not found",
            }
        ),
        404,
    )


def create_app():
    """
    factory used by tests or wsgi servers
    """
    return app


if __name__ == "__main__":
    port = int(os.environ.get("FEATURE_FLAG_PORT", "5005"))
    app.run(host="0.0.0.0", port=port, debug=False)
