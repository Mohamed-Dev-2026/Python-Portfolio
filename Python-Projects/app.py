import os
import random
import string
from flask import Flask, request, redirect, render_template, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///urls.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<URL {self.short_code}>"


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if not URL.query.filter_by(short_code=code).first():
            return code


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = request.form.get("url", "").strip()
        if not original_url:
            flash("Please enter a URL.", "error")
            return redirect(url_for("index"))

        if not original_url.startswith(("http://", "https://")):
            original_url = "https://" + original_url

        existing = URL.query.filter_by(original_url=original_url).first()
        if existing:
            short_url = request.host_url + existing.short_code
            return render_template("index.html", short_url=short_url, urls=get_recent_urls())

        short_code = generate_short_code()
        new_url = URL(original_url=original_url, short_code=short_code)
        db.session.add(new_url)
        db.session.commit()

        short_url = request.host_url + short_code
        return render_template("index.html", short_url=short_url, urls=get_recent_urls())

    return render_template("index.html", urls=get_recent_urls())


def get_recent_urls():
    return URL.query.order_by(URL.created_at.desc()).limit(10).all()


@app.route("/<short_code>")
def redirect_to_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first_or_404()
    url.clicks += 1
    db.session.commit()
    return redirect(url.original_url)


@app.route("/stats/<short_code>")
def stats(short_code):
    url = URL.query.filter_by(short_code=short_code).first_or_404()
    return render_template("stats.html", url=url)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
