from flask import Blueprint, request, jsonify

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"], strict_slashes=False)
def search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "Please provide a 'q' query parameter."}), 400

    try:
        from ddgs import DDGS
    except ImportError:
        return jsonify({
            "error": "Search dependency not installed. Run: pip install ddgs"
        }), 500

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=8))
    except Exception as err:
        return jsonify({"error": f"Search failed: {err}"}), 502

    results = [
        {
            "title": r.get("title") or "Untitled",
            "url": r.get("href") or r.get("link") or "",
            "snippet": r.get("body", ""),
        }
        for r in raw_results
    ]
    return jsonify({"query": query, "results": results})
