from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
 
from routes.generate import generate_bp
from routes.library import library_bp
from routes.translate import translate_bp
from routes.search import search_bp
from routes.saved import saved_bp
from routes.upload import upload_bp
 
load_dotenv()
 
app = Flask(__name__)
CORS(app)  # wide open for hackathon speed — tighten if you have time
 
app.register_blueprint(generate_bp, url_prefix="/api/generate")
app.register_blueprint(library_bp, url_prefix="/api/library")
app.register_blueprint(translate_bp, url_prefix="/api/translate")
app.register_blueprint(search_bp, url_prefix="/api/search")
app.register_blueprint(saved_bp, url_prefix="/api/saved")
app.register_blueprint(upload_bp, url_prefix="/api/upload")
 
 
@app.get("/api/health")
def health():
    return {"status": "ok"}
 
 
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3001))
    app.run(host="0.0.0.0", port=port, debug=True)
 