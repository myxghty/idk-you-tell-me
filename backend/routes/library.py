from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

library_bp = Blueprint("library", __name__)

# In-memory store — resets on server restart. Fine for a hackathon demo;
# swap for a real DB only if you have spare time, it is not worth the risk.
modules = []
next_id = 1


@library_bp.route("/", methods=["POST"])
def save_module():
    global next_id

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    source_text = body.get("source_text", "")
    data = body.get("data")

    if not title or not data:
        return jsonify({"error": "'title' and 'data' are required."}), 400

    entry = {
        "id": next_id,
        "title": title,
        "source_text": source_text,
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    next_id += 1
    modules.append(entry)

    return jsonify(entry), 201


@library_bp.route("/", methods=["GET"])
def list_modules():
    summaries = [
        {"id": m["id"], "title": m["title"], "created_at": m["created_at"]}
        for m in modules
    ]
    return jsonify(summaries)


@library_bp.route("/<int:module_id>", methods=["GET"])
def get_module(module_id):
    entry = next((m for m in modules if m["id"] == module_id), None)
    if not entry:
        return jsonify({"error": "Module not found"}), 404
    return jsonify(entry)
