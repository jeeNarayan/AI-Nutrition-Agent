"""
app.py — Flask application entry point for the Nutrition Agent.

Run locally:
    flask --app app run --debug

Production (Gunicorn):
    gunicorn app:app --bind 0.0.0.0:8080 --workers 2
"""

from flask import Flask, render_template

import config
import db
from routes.chat      import chat_bp
from routes.nutrition import nutrition_bp
from routes.bmi       import bmi_bp
from routes.profiles  import profiles_bp

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# Register API blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(nutrition_bp)
app.register_blueprint(bmi_bp)
app.register_blueprint(profiles_bp)

# Initialise the database on startup
db.init_db()


# ─────────────────────────────────────────────────────────────────
#  Page routes
# ─────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/meal-plan")
def meal_plan():
    return render_template("meal_plan.html")


@app.get("/bmi")
def bmi():
    return render_template("bmi.html")


@app.get("/profiles")
def profiles():
    return render_template("profiles.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
