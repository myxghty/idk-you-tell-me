from flask import Blueprint, request, jsonify
from utils.ai import translate_text

translate_bp = Blueprint("translate", __name__)


@translate_bp.route("/", methods=["POST"], strict_slashes=False)
def translate():
    body = request.get_json(silent=True) or {}
    text = body.get("text")
    target_language = body.get("target_language")

    translation, error = translate_text(text, target_language)
    if error:
        status = error.pop("status")
        return jsonify(error), status

    return jsonify({"translation": translation})
