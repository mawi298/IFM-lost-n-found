


import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

# Initialize app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

# Database configuration
# Render automatically provides DATABASE_URL when you add a PostgreSQL service
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    # Local PostgreSQL (for development)
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "student")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "lostfound_db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File uploads
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Database
db = SQLAlchemy(app)

# Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    contact = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    date_lost_found = db.Column(db.DateTime, default=datetime.utcnow)
    image_filename = db.Column(db.String(100))  # file name in /static/uploads


# Ensure tables exist
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables ready")
    except Exception as e:
        print("⚠️ Could not create tables:", e)


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    items = Item.query.order_by(Item.id.desc()).all()
    return render_template("home.html", items=items)


@app.route("/add-item")
def add_item():
    return render_template("add_item.html")


@app.route("/add-lost", methods=["GET", "POST"])
def add_lost():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        contact = request.form.get("contact")
        location = request.form.get("location")
        date_lf = request.form.get("date_lf")
        image = request.files.get("photo")

        filename = None
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        new_item = Item(
            item_type="lost",
            title=title,
            description=description,
            contact=contact,
            location=location,
            date_lost_found=datetime.strptime(date_lf, "%Y-%m-%d") if date_lf else datetime.utcnow(),
            image_filename=filename
        )

        try:
            db.session.add(new_item)
            db.session.commit()
            flash("Lost item posted!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

        return redirect(url_for("home"))

    return render_template("add_lost.html")


@app.route("/add-found", methods=["GET", "POST"])
def add_found():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        contact = request.form.get("contact")
        location = request.form.get("location")
        date_lf = request.form.get("date_lf")
        image = request.files.get("photo")

        filename = None
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        new_item = Item(
            item_type="found",
            title=title,
            description=description,
            contact=contact,
            location=location,
            date_lost_found=datetime.strptime(date_lf, "%Y-%m-%d") if date_lf else datetime.utcnow(),
            image_filename=filename
        )

        try:
            db.session.add(new_item)
            db.session.commit()
            flash("Found item posted!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

        return redirect(url_for("home"))

    return render_template("add_found.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    items = []
    if query:
        items = Item.query.filter(
            Item.title.ilike(f"%{query}%") |
            Item.description.ilike(f"%{query}%") |
            Item.location.ilike(f"%{query}%")
        ).order_by(Item.id.desc()).all()
    return render_template("search.html", items=items, query=query)


@app.route("/item/<int:item_id>")
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template("item_detail.html", item=item)


# Health check route
@app.route("/ping")
def ping():
    return "✅ Flask app is running!"


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
