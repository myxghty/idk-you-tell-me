from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

saved_bp = Blueprint("saved", __name__)

# In-memory store — same pattern as routes/library.py. Resets on server
# restart; fine for a demo, swap for a real DB only if you have time.
saved_items = []
next_id = 1


@saved_bp.route("/", methods=["POST"], strict_slashes=False)
def save_item():
    global next_id

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return jsonify({"error": "'title' is required."}), 400

    entry = {
        "id": next_id,
        "title": title,
        "url": body.get("url"),
        "snippet": body.get("snippet", ""),
        "source": body.get("source", "manual"),  # 'search' | 'recommended' | 'manual'
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    next_id += 1
    saved_items.append(entry)

    return jsonify(entry), 201


@saved_bp.route("/", methods=["GET"], strict_slashes=False)
def list_saved():
    return jsonify(saved_items)


@saved_bp.route("/<int:item_id>", methods=["DELETE"], strict_slashes=False)
def delete_saved(item_id):
    global saved_items
    before = len(saved_items)
    saved_items = [i for i in saved_items if i["id"] != item_id]
    if len(saved_items) == before:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"deleted": item_id})
