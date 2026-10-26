from flask import Flask, jsonify
from flask_cors import CORS
from routes.upload_routes import bp as upload_bp
from routes.chat_routes import bp as chat_bp
from routes.schedule_routes import bp as schedule_bp
from routes.email_routes import bp as email_bp
from routes.feedback_routes import bp as feedback_bp
from routes.report_routes import bp as report_bp

app = Flask(__name__)
CORS(app)
for b in (upload_bp, chat_bp, schedule_bp, email_bp, feedback_bp, report_bp):
    app.register_blueprint(b)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Intern Review Bot API running"})

@app.errorhandler(Exception)
def err(e):
    return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
