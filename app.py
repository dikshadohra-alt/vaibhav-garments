from dataclasses import fields
from itertools import product

from flask_wtf.csrf import CSRFProtect

import os

import sqlite3

from functools import wraps

from urllib.parse import quote

from pathlib import Path

 

 

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

 

from werkzeug.utils import secure_filename

 

from werkzeug.security import generate_password_hash, check_password_hash

 

BASE_DIR = Path(__file__).resolve().parent

 

UPLOAD_DIR = BASE_DIR / "static" / "uploads"

 

 

 

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

 

app = Flask(__name__)

 

 

 

app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")

 

 

 

csrf = CSRFProtect(app)

 

 

 

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

 

 

 

app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

 

 

 

 

 

 

 

DB_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "store.db"))

 

 

 

WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "7015769205")

 

 

 

INSTAGRAM_URL = os.environ.get("INSTAGRAM_URL", "https://www.instagram.com/vaibhav_garments_padha_0/")

 

 

 

SHOP_ADDRESS = os.environ.get("SHOP_ADDRESS", "Village Padha, Tehsil Assandh, District Karnal, Haryana - 132036")

 

 

 

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

 

 

 

 

 

 

 

def get_db():

 

 

 

    conn = sqlite3.connect(DB_PATH)

 

 

 

    conn.row_factory = sqlite3.Row

 

 

 

    conn.execute("PRAGMA foreign_keys = ON")

 

 

 

    return conn

 

 

 

 

 

 

 

 

 

 

 

def init_db():

 

 

 

    global WHATSAPP_NUMBER, INSTAGRAM_URL, SHOP_ADDRESS

 

 

 

    with get_db() as db:

 

 

 

        db.execute("""CREATE TABLE IF NOT EXISTS products (

 

 

 

            id INTEGER PRIMARY KEY AUTOINCREMENT,

 

 

 

            name TEXT NOT NULL,

 

 

 

            category TEXT NOT NULL CHECK(category IN ('Women','Men','Kids','Beauty')),

 

 

 

            price REAL NOT NULL,

 

 

 

            old_price REAL DEFAULT 0,

 

 

 

            description TEXT DEFAULT '',

 

 

 

            fabric TEXT DEFAULT '',

 

 

 

            sizes TEXT DEFAULT '',

 

 

 

            colours TEXT DEFAULT 'Blue, Black',

 

 

 

            image TEXT DEFAULT '',

 

 

 

            featured INTEGER DEFAULT 0,

 

 

 

            active INTEGER DEFAULT 1,

 

 

 

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

 

 

 

        )""")

 

 

 

        db.execute("""CREATE TABLE IF NOT EXISTS admin_users (

 

 

 

            id INTEGER PRIMARY KEY AUTOINCREMENT,

 

 

 

            username TEXT UNIQUE NOT NULL,

 

 

 

            password_hash TEXT NOT NULL

 

 

 

        )""")

 

 

 

        db.execute("""

 

 

 

            CREATE TABLE IF NOT EXISTS store_settings (

 

 

 

                id INTEGER PRIMARY KEY CHECK (id = 1),

 

 

 

                whatsapp_number TEXT NOT NULL,

 

 

 

                instagram_url TEXT NOT NULL DEFAULT '',

 

 

 

                shop_address TEXT NOT NULL DEFAULT ''

 

 

 

            )

 

 

 

        """)

 

 

 

        db.execute("""

 

 

 

            INSERT OR IGNORE INTO store_settings

 

 

 

            (id, whatsapp_number, instagram_url, shop_address)

 

 

 

            VALUES (1, ?, ?, ?)

 

 

 

        """, (WHATSAPP_NUMBER, INSTAGRAM_URL, SHOP_ADDRESS))

 

 

 

        saved_settings = db.execute(

 

 

 

            "SELECT * FROM store_settings WHERE id = 1"

 

 

 

        ).fetchone()

 

 

 

        if saved_settings:

 

 

 

            WHATSAPP_NUMBER = saved_settings["whatsapp_number"]

 

 

 

            INSTAGRAM_URL = saved_settings["instagram_url"]

 

 

 

            SHOP_ADDRESS = saved_settings["shop_address"]

 

 

 

        # Migrate an older products table so it also accepts the Beauty category.

 

 

 

        # SQLite cannot alter a CHECK constraint directly, so rebuild the table

 

 

 

        # while preserving all existing products and IDs.

 

 

 

        schema_row = db.execute(

 

 

 

            "SELECT sql FROM sqlite_master WHERE type='table' AND name='products'"

 

 

 

        ).fetchone()

 

 

 

        if schema_row and "'Beauty'" not in (schema_row["sql"] or ""):

 

 

 

            db.execute("""

 

 

 

                CREATE TABLE products_new (

 

 

 

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

 

 

 

                    name TEXT NOT NULL,

 

 

 

                    category TEXT NOT NULL CHECK(category IN ('Women','Men','Kids','Beauty')),

 

 

 

                    price REAL NOT NULL,

 

 

 

                    old_price REAL DEFAULT 0,

 

 

 

                    description TEXT DEFAULT '',

 

 

 

                    fabric TEXT DEFAULT '',

 

 

 

                    sizes TEXT DEFAULT '',

 

 

 

                    colours TEXT DEFAULT 'Blue, Black',

 

 

 

                    image TEXT DEFAULT '',

 

 

 

                    featured INTEGER DEFAULT 0,

 

 

 

                    active INTEGER DEFAULT 1,

 

 

 

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

 

 

 

                )

 

 

 

            """)

 

 

 

            db.execute("""

 

 

 

                INSERT INTO products_new

 

 

 

                (id, name, category, price, old_price, description, fabric,

 

 

 

                 sizes, colours, image, featured, active, created_at)

 

 

 

                SELECT id, name, category, price, old_price, description, fabric,

 

 

 

                       sizes, colours, image, featured, active, created_at

 

 

 

                FROM products

 

 

 

            """)

 

 

 

            db.execute("DROP TABLE products")

 

 

 

            db.execute("ALTER TABLE products_new RENAME TO products")

 

 

 

 

 

 

 

        count = db.execute("SELECT COUNT(*) AS n FROM admin_users").fetchone()["n"]

 

 

 

        if count == 0:

 

 

 

            username = os.environ.get("ADMIN_USERNAME", "admin")

 

 

 

            password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

 

 

 

            db.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",

 

 

 

                       (username, generate_password_hash(password)))

 

 

 

        products_count = db.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]

 

 

 

        if products_count == 0:

 

 

 

            samples = [

 

 

 

                ("Classic Casual Shirt", "Men", 799, 999, "Everyday comfort with a smart fit.", "Cotton blend", "M, L, XL, XXL", "White, Blue, Black", "", 1),

 

 

 

                ("Elegant Everyday Kurti", "Women", 699, 899, "Comfortable style for everyday wear.", "Rayon", "S, M, L, XL, XXL", "Yellow, Blue, Pink", "", 1),

 

 

 

                ("Kids Printed Outfit", "Kids", 599, 749, "A cheerful and comfortable outfit for kids.", "Cotton", "2-3Y, 4-5Y, 6-7Y, 8-9Y", "Blue, Yellow, Pink", "", 1),

 

 

 

                ("Lightweight Denim Jacket", "Men", 1299, 1599, "A versatile layer for casual looks.", "Denim", "M, L, XL", "Blue, Black", "", 0),

 

 

 

                ("Floral Dress", "Women", 999, 1299, "A fresh floral look for outings.", "Georgette", "S, M, L, XL", "Pink, Green, Black", "", 0),

 

 

 

                ("Kids Festive Set", "Kids", 899, 1099, "Festive style with a comfortable finish.", "Cotton blend", "2-3Y, 4-5Y, 6-7Y", "Cream, Maroon, Blue", "", 0),

 

 

 

                ("Everyday Beauty Essentials", "Beauty", 499, 649, "Beauty essentials for your everyday routine.", "Cosmetics", "Standard", "Assorted", "", 0),

 

 

 

            ]

 

 

 

            db.executemany("""INSERT INTO products

 

 

 

                (name, category, price, old_price, description, fabric, sizes, colours, image, featured)

 

 

 

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", samples)

 

 

 

 

 

 

 

def admin_required(view):

 

 

 

    @wraps(view)

 

 

 

    def wrapped(*args, **kwargs):

 

 

 

        if not session.get("admin_id"):

 

 

 

            return redirect(url_for("admin_login", next=request.path))

 

 

 

        return view(*args, **kwargs)

 

 

 

    return wrapped

 

 

 

 

 

 

 

def allowed_file(filename):

 

 

 

    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

 

 

 

 

 

 

 

@app.context_processor

 

 

 

def inject_globals():

 

 

 

    return {

 

 

 

        "shop_name": "VAIBHAV GARMENTS",

 

 

 

        "whatsapp_number": WHATSAPP_NUMBER,

 

 

 

        "instagram_url": INSTAGRAM_URL,

 

 

 

        "shop_address": SHOP_ADDRESS,

 

 

 

    }

 

 

 

 

 

 

 

@app.route("/")

 

 

 

def home():

 

 

 

    category = request.args.get("category", "").strip()

 

 

 

    search = request.args.get("q", "").strip()

 

 

 

    with get_db() as db:

 

 

 

        sql = "SELECT * FROM products WHERE active=1"

 

 

 

        params = []

 

 

 

        if category in ("Women", "Men", "Kids", "Beauty"):

 

 

 

            sql += " AND category=?"

 

            params.append(category)

 

 

 

        if search:

 

 

 

            sql += " AND (name LIKE ? OR description LIKE ? OR fabric LIKE ?)"

 

 

 

            params.extend([f"%{search}%"] * 3)

 

 

 

        sql += " ORDER BY featured DESC, id DESC"

 

 

 

        products = db.execute(sql, params).fetchall()

 

 

 

        featured = db.execute("SELECT * FROM products WHERE active=1 AND featured=1 ORDER BY id DESC LIMIT 3").fetchall()

 

 

 

    return render_template("home.html", products=products, featured=featured, selected_category=category, search=search)

 

 

 

 

 

 

 

@app.route("/product/<int:product_id>")

 

 

 

def product_detail(product_id):

 

 

 

    with get_db() as db:

 

 

 

        product = db.execute(

 

            "SELECT * FROM products WHERE id=? AND active=1",

 

            (product_id,)

 

        ).fetchone()

 

 

 

        if not product:

 

            abort(404)

    product_images = db.execute(
    "SELECT image FROM product_images WHERE product_id=? ORDER BY id ASC",
    (product_id,)
).fetchall()

 

 

        # Show other active products from the same category only.

 

    related_products = db.execute(

 

            """SELECT * FROM products

 

               WHERE active=1 AND category=? AND id<>?

 

               ORDER BY featured DESC, id DESC

 

               LIMIT 8""",

 

            (product["category"], product_id)

 

        ).fetchall()

 

 

 

    return render_template(

 

        "product.html",

 

        product=product,
related_products=related_products,
product_images=product_images
 

    )

 

 

 

 

 

 

 

 

 

 

 

@app.route("/wishlist")

 

 

 

def wishlist_page():

 

 

 

    with get_db() as db:

 

 

 

        rows = db.execute(

 

 

 

            "SELECT * FROM products WHERE active=1 ORDER BY id DESC"

 

 

 

        ).fetchall()

 

 

 

 

 

 

 

    wishlist_products = []

 

 

 

 

 

 

 

    for product in rows:

 

 

 

        wishlist_products.append({

 

 

 

            "id": product["id"],

 

 

 

            "name": product["name"],

 

 

 

            "category": product["category"],

 

 

 

            "price": product["price"],

 

 

 

            "image_url": (

 

 

 

                url_for("static", filename="uploads/" + product["image"])

 

 

 

                if product["image"] else ""

 

 

 

            ),

 

 

 

            "product_url": url_for(

 

 

 

                "product_detail", product_id=product["id"]

 

 

 

            ),

 

 

 

            "order_url": url_for(

 

 

 

                "order_product", product_id=product["id"]

 

 

 

            )

 

 

 

        })

 

 

 

 

 

 

 

    return render_template(

 

 

 

        "wishlist.html",

 

 

 

        wishlist_products=wishlist_products

 

 

 

    )

 

 

 

 

 

 

 

@app.route("/cart")

 

 

 

def cart_page():

 

 

 

    return render_template("cart.html")

 

 

 

 

 

 

 

 

 

 

 

@app.route("/order/<int:product_id>", methods=["GET", "POST"])

 

 

 

@csrf.exempt

 

 

 

def order_product(product_id):

 

 

 

    with get_db() as db:

 

 

 

        product = db.execute("SELECT * FROM products WHERE id=? AND active=1", (product_id,)).fetchone()

 

 

 

    if not product:

 

 

 

        abort(404)

 

 

 

    if request.method == "POST":

 

 

 

        fields = {

 

 

 

            "name": request.form.get("name", "").strip(),

 

 

 

            "mobile": request.form.get("mobile", "").strip(),

 

 

 

            "email": request.form.get("email", "").strip(),

 

 

 

            "address": request.form.get("address", "").strip(),

 

 

 

            "city": request.form.get("city", "").strip(),

 

 

 

            "pincode": request.form.get("pincode", "").strip(),

 

 

 

            "size": request.form.get("size", "").strip(),

 

 

 

            "colour": request.form.get("colour", "").strip(),

 

 

 

            "fabric": request.form.get("fabric", "").strip() or product["fabric"],


            "quantity": request.form.get("quantity", "1").strip(),

            "note": request.form.get("note", "").strip(),

        }


        # Size and colour are required only when the product has those options
        required_fields = ["name", "mobile", "address", "city", "pincode"]

        available_sizes = [
            s.strip()
            for s in (product["sizes"] or "").split(",")
            if s.strip()
        ]

        available_colours = [
            c.strip()
            for c in (product["colours"] or "").split(",")
            if c.strip()
        ]

        if available_sizes:
            required_fields.append("size")
        else:
            fields["size"] = "Not applicable"

        if available_colours:
            required_fields.append("colour")
        else:
            fields["colour"] = "Not applicable"

        if not all(fields.get(k) for k in required_fields):
            flash("Please fill in all required fields.", "error")
            return render_template("order.html", product=product, form=fields)


        try:

 
            qty = max(1, min(20, int(fields["quantity"])))

        except ValueError:

            qty = 1

        total = float(product["price"]) * qty

        image_url = request.url_root.rstrip("/") + url_for("static", filename="uploads/" + product["image"]) if product["image"] else "Product image available on the website product page"

        product_url = request.url_root.rstrip("/") + url_for("product_detail", product_id=product["id"])


        message = (

            "Hello Vaibhav Garments! I want to place an order.\n\n"

            f"Product: {product['name']}\nCategory: {product['category']}\n"

            f"Product page: {product_url}\nProduct image: {image_url}\n"

 

 

 

            f"Price: Rs. {float(product['price']):.2f}\nQuantity: {qty}\n"

 

           f"Size: {fields.get('size') or 'Not applicable'}\n"
f"Colour: {fields.get('colour') or 'Not applicable'}\n"
f"Fabric: {fields.get('fabric') or 'Not specified'}\n"

 

 

 

            f"Estimated total: Rs. {total:.2f} (delivery, if applicable, to be confirmed)\n\n"

 

 

 

            f"Customer name: {fields['name']}\nMobile/WhatsApp: {fields['mobile']}\n"

 

 

 

            f"Email: {fields['email'] or 'Not provided'}\n"

 

 

 

            f"Delivery address: {fields['address']}\nCity: {fields['city']}\nPincode: {fields['pincode']}\n"

 

 

 

            f"Special note: {fields['note'] or 'None'}"

 

 

 

        )

 

 

 

        return redirect("https://wa.me/" + "".join(c for c in WHATSAPP_NUMBER if c.isdigit()) + "?text=" + quote(message))

 

 

 

    return render_template("order.html", product=product, form={})

 

 

 

 

 

 

 

@app.route("/admin")

 

 

 

@admin_required

 

 

 

def admin_dashboard():

 

 

 

    with get_db() as db:

 

 

 

        products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()

 

 

 

        active_count = db.execute("SELECT COUNT(*) AS n FROM products WHERE active=1").fetchone()["n"]

 

 

 

    return render_template("admin/dashboard.html", products=products, active_count=active_count)

 

 

 

 

 

 

 

@app.route("/admin/login", methods=["GET", "POST"])

 

 

 

def admin_login():

 

 

 

    if session.get("admin_id"):

 

 

 

        return redirect(url_for("admin_dashboard"))

 

 

 

    if request.method == "POST":

 

 

 

        username = request.form.get("username", "").strip()

 

 

 

        password = request.form.get("password", "")

 

 

 

        with get_db() as db:

 

 

 

            admin = db.execute("SELECT * FROM admin_users WHERE username=?", (username,)).fetchone()

 

 

 

        if admin and check_password_hash(admin["password_hash"], password):

 

 

 

            session.clear()

 

 

 

            session["admin_id"] = admin["id"]

 

 

 

            session["admin_username"] = admin["username"]

 

 

 

            return redirect(url_for("admin_dashboard"))

 

 

 

        flash("Incorrect username or password.", "error")

 

 

 

    return render_template("admin/login.html")

@app.route("/admin/logout")

 

 

 

def admin_logout():

 

 

 

    session.clear()

 

 

 

    flash("You have been logged out.", "success")

 

 

 

    return redirect(url_for("home"))

 

 

 

 

 

 

 

@app.route("/admin/product/new", methods=["GET", "POST"])

 

 

 

@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])

 

 

 

@admin_required

 

 

 

def edit_product(product_id=None):

 

 

 

    with get_db() as db:

 

 

 

        existing = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone() if product_id else None

 

 

 

    if product_id and not existing:

 

 

 

        abort(404)

 

 

 

    if request.method == "POST":

 

 

 

        name = request.form.get("name", "").strip()

 

 

 

        category = request.form.get("category", "")

 

 

 

        try:

 

 

 

            price = float(request.form.get("price", "0"))

 

 

 

            old_price = float(request.form.get("old_price", "0") or 0)

 

 

 

        except ValueError:

 

 

 

            price, old_price = -1, 0

 

 

 

        if not name or category not in ("Women", "Men", "Kids", "Beauty") or price < 0:

 

 

 

            flash("Enter a product name, valid category and valid price.", "error")

 

 

 

            return render_template("admin/product_form.html", product=existing, editing=bool(existing))

 

 

 

        image_name = existing["image"] if existing else ""

uploaded_images = [
    img for img in request.files.getlist("images")
    if img and img.filename
]

if any(not allowed_file(img.filename) for img in uploaded_images):
    flash("Only PNG, JPG, JPEG, WEBP or GIF images are allowed.", "error")
    return render_template(
        "admin/product_form.html",
        product=existing,
        editing=bool(existing)
    )

saved_images = []

for img in uploaded_images:
    filename = secure_filename(img.filename)
    stem, ext = os.path.splitext(filename)

    unique_name = f"{stem[:50]}_{os.urandom(4).hex()}{ext.lower()}"
    img.save(UPLOAD_DIR / unique_name)
    saved_images.append(unique_name)

if saved_images:
    image_name = saved_images[0]

 

 

 

        values = (

 

 

 

            name, category, price, old_price,

 

 

 

            request.form.get("description", "").strip(),

 

 

 

            request.form.get("fabric", "").strip(),

 

 

 

            request.form.get("sizes", "").strip(),

 

 

 

            request.form.get("colours", "").strip(),

 

 

 

            image_name, 1 if request.form.get("featured") else 0,

 

 

 

            1 if request.form.get("active") else 0

 

 

 

        )

 

 

 

        with get_db() as db:
    if existing:
        saved_product_id = product_id

        db.execute("""
            UPDATE products
            SET name=?, category=?, price=?, old_price=?,
                description=?, fabric=?, sizes=?, colours=?,
                image=?, featured=?, active=?
            WHERE id=?
        """, values + (product_id,))

    else:
        cursor = db.execute("""
            INSERT INTO products
            (name, category, price, old_price, description, fabric,
             sizes, colours, image, featured, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

        saved_product_id = cursor.lastrowid

    for saved_image in saved_images:
        db.execute("""
            INSERT INTO product_images (product_id, image)
            VALUES (?, ?)
        """, (saved_product_id, saved_image))
 

 with get_db() as db:
    if existing:
        saved_product_id = product_id
    else:
        saved_product_id = db.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

    for saved_image in saved_images:
        db.execute(
            "INSERT INTO product_images (product_id, image) VALUES (?, ?)",
            (saved_product_id, saved_image)
        )

        flash("Product saved successfully.", "success")

 

 

 

        return redirect(url_for("admin_dashboard"))

 

 

 

    return render_template("admin/product_form.html", product=existing, editing=bool(existing))

 

 

 

 

 

 

 

@app.route("/admin/product/<int:product_id>/delete", methods=["POST"])

 

 

 

@admin_required

 

 

 

def delete_product(product_id):

 

 

 

    with get_db() as db:

 

 

 

        db.execute("DELETE FROM products WHERE id=?", (product_id,))

 

 

 

    flash("Product deleted.", "success")

 

    return redirect(url_for("admin_dashboard")) 

@app.route("/admin/settings", methods=["GET", "POST"])

@admin_required


def admin_settings():

 
    global WHATSAPP_NUMBER, INSTAGRAM_URL, SHOP_ADDRESS

 
 

    if request.method == "POST":

 

        whatsapp = request.form.get("whatsapp_number", "").strip()


        instagram = request.form.get("instagram_url", "").strip()


        address = request.form.get("shop_address", "").strip()

 

 

        if not whatsapp or len(whatsapp) > 20:

 
 

            flash("Enter a valid WhatsApp number (maximum 20 characters).", "error")

 

            return redirect(url_for("admin_settings"))

 

        if len(instagram) > 500 or len(address) > 1000:

 
            flash("Instagram URL or shop address is too long.", "error")

 
            return redirect(url_for("admin_settings"))


        if instagram and not instagram.startswith("https://"):


            flash("Please enter an Instagram URL starting with https://.", "error")

            return redirect(url_for("admin_settings"))
        with get_db() as db:

            db.execute("""
                UPDATE store_settings

                SET whatsapp_number = ?, instagram_url = ?, shop_address = ?

                WHERE id = 1
            """, (whatsapp, instagram, address))

        WHATSAPP_NUMBER = whatsapp

        INSTAGRAM_URL = instagram

        SHOP_ADDRESS = address

        flash("Store settings saved permanently.", "success")

        return redirect(url_for("admin_settings"))

    with get_db() as db:


        settings = db.execute(


            "SELECT * FROM store_settings WHERE id = 1"

        ).fetchone()

    if settings:

        WHATSAPP_NUMBER = settings["whatsapp_number"]


        INSTAGRAM_URL = settings["instagram_url"]

 

        SHOP_ADDRESS = settings["shop_address"]


    return render_template(


        "admin/settings.html",

        whatsapp=WHATSAPP_NUMBER,

        instagram=INSTAGRAM_URL,

        address=SHOP_ADDRESS


    )



@app.route("/admin/change-password", methods=["POST"])

@admin_required

def admin_change_password():

    """Securely change the password for the currently signed-in admin."""

    current_password = request.form.get("current_password", "")

    new_password = request.form.get("new_password", "")

    confirm_password = request.form.get("confirm_password", "")

 

    if not current_password or not new_password or not confirm_password:

        flash("Please fill in all password fields.", "error")

        return redirect(url_for("admin_settings"))

 

    if len(new_password) < 10:

        flash("New password must be at least 10 characters long.", "error")

        return redirect(url_for("admin_settings"))

 

    if len(new_password) > 128:

        flash("New password must be 128 characters or fewer.", "error")

        return redirect(url_for("admin_settings"))

 

    if new_password != confirm_password:

        flash("New password and confirmation do not match.", "error")

        return redirect(url_for("admin_settings"))

 

    with get_db() as db:

        admin = db.execute(

            "SELECT id, password_hash FROM admin_users WHERE id = ?",

            (session.get("admin_id"),)

        ).fetchone()

 

        if not admin or not check_password_hash(admin["password_hash"], current_password):

            flash("Current password is incorrect.", "error")

            return redirect(url_for("admin_settings"))

 

        if check_password_hash(admin["password_hash"], new_password):

            flash("Choose a new password different from your current password.", "error")

            return redirect(url_for("admin_settings"))

 

        db.execute(

            "UPDATE admin_users SET password_hash = ? WHERE id = ?",

            (generate_password_hash(new_password), admin["id"])

        )

 

    flash("Admin password changed successfully. Use the new password next time you log in.", "success")

    return redirect(url_for("admin_settings"))


@app.errorhandler(404)

def not_found(error):

  return render_template("404.html"), 404

init_db()


if __name__ == "__main__":


    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true", host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))