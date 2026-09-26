from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from routes.generate import generate_bp
from routes.library import library_bp

load_dotenv()

app = Flask(__name__)
CORS(app)  # wide open for hackathon speed — tighten if you have time

app.register_blueprint(generate_bp, url_prefix="/api/generate")
app.register_blueprint(library_bp, url_prefix="/api/library")


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3001))
    app.run(host="0.0.0.0", port=port, debug=True)
