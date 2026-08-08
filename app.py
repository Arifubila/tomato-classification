from flask import Flask, render_template, request, redirect, url_for, flash
import os
import uuid
import cv2
import joblib
import sqlite3
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename

from database import (
    create_table,
    insert_history
)

app = Flask(__name__)

app.secret_key = "tomato-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

create_table()

model = joblib.load(MODEL_PATH)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

create_table()

# ======================================
# Load Decision Tree Model
# ======================================

model = joblib.load("model.pkl")


# ======================================
# Helper
# ======================================

def allowed_file(filename):

    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_hsv(image_path):

    image = cv2.imread(image_path)

    image = cv2.resize(image, (224, 224))

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    h = np.mean(hsv[:, :, 0])

    s = np.mean(hsv[:, :, 1])

    v = np.mean(hsv[:, :, 2])

    return h, s, v


def classify(image_path):

    h, s, v = extract_hsv(image_path)

    feature = np.array([[h, s, v]])

    prediction = model.predict(feature)[0]

    probability = model.predict_proba(feature)

    confidence = np.max(probability) * 100

    return prediction, confidence, h, s, v


# ======================================
# HOME
# ======================================

@app.route("/")
def index():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM history")

    total = cursor.fetchone()[0]

    cursor.execute("""

    SELECT COUNT(*)

    FROM history

    WHERE prediction='matang'

    """)

    matang = cursor.fetchone()[0]

    cursor.execute("""

    SELECT COUNT(*)

    FROM history

    WHERE prediction='mentah'

    """)

    mentah = cursor.fetchone()[0]

    conn.close()

    return render_template(

        "index.html",

        total=total,

        matang=matang,

        mentah=mentah

    )


# ======================================
# DATASET
# ======================================

@app.route("/dataset")
def dataset():

    matang_folder = os.path.join(
        BASE_DIR,
        "static",
        "dataset",
        "matang"
    )

    mentah_folder = os.path.join(
        BASE_DIR,
        "static",
        "dataset",
        "mentah"
    )

    matang = []
    mentah = []

    if os.path.exists(matang_folder):
        matang = os.listdir(matang_folder)

    if os.path.exists(mentah_folder):
        mentah = os.listdir(mentah_folder)

    return render_template(
        "dataset.html",
        matang=matang,
        mentah=mentah,
        total=len(matang) + len(mentah)
    )


# ======================================
# EVALUASI
# ======================================

@app.route("/evaluasi")
def evaluasi():

    accuracy = 88
    precision = 0.88
    recall = 0.88
    f1 = 0.87

    matrix = [

        [18, 2],

        [3, 17]

    ]

    return render_template(

        "evaluasi.html",

        accuracy=accuracy,

        precision=precision,

        recall=recall,

        f1=f1,

        matrix=matrix

    )
   
    # ======================================
# KLASIFIKASI
# ======================================

@app.route("/klasifikasi", methods=["GET", "POST"])
def klasifikasi():

    if request.method == "POST":

        if "image" not in request.files:

            flash("Silakan pilih gambar terlebih dahulu.", "danger")
            return redirect(request.url)

        file = request.files["image"]

        if file.filename == "":

            flash("File belum dipilih.", "warning")
            return redirect(request.url)

        if not allowed_file(file.filename):

            flash("Format file harus JPG, JPEG, atau PNG.", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)

        ext = filename.rsplit(".", 1)[1]

        new_name = f"{uuid.uuid4().hex}.{ext}"

        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            new_name
        )

        file.save(save_path)

        start = datetime.now()

        prediction, confidence, h, s, v = classify(save_path)

        finish = datetime.now()

        process_time = (
            finish - start
        ).total_seconds()

        insert_history(

    filename=new_name,

    h=round(h,2),

    s=round(s,2),

    v=round(v,2),

    prediction=prediction,

    confidence=round(confidence,2),

    process_time=round(process_time,4)

)

        return render_template(

            "klasifikasi.html",

            image=new_name,

            prediction=prediction.upper(),

            confidence=round(confidence,2),

            hue=round(h,2),

            saturation=round(s,2),

            value=round(v,2),

            process_time=process_time

        )

    return render_template("klasifikasi.html")


# ======================================
# RIWAYAT
# ======================================

@app.route("/riwayat")
def riwayat():

    keyword = request.args.get("search", "").strip()

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if keyword == "":

        cursor.execute("""

        SELECT *

        FROM history

        ORDER BY id DESC

        """)

    else:

        cursor.execute("""

        SELECT *

        FROM history

        WHERE prediction LIKE ?

        ORDER BY id DESC

        """, (f"%{keyword}%",))

    data = cursor.fetchall()

    conn.close()

    return render_template(

        "riwayat.html",

        history=data,

        keyword=keyword

    )


# ======================================
# HAPUS RIWAYAT
# ======================================

@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM history WHERE id=?",

        (id,)

    )

    conn.commit()

    conn.close()

    flash("Riwayat berhasil dihapus.", "success")

    return redirect(url_for("riwayat"))


# ======================================
# HAPUS SEMUA
# ======================================

@app.route("/delete-all")
def delete_all():

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM history")

    conn.commit()

    conn.close()

    flash("Semua riwayat berhasil dihapus.", "success")

    return redirect(url_for("riwayat"))

# ======================================
# TENTANG
# ======================================

@app.route("/tentang")
def tentang():

    info = {

        "judul": "Implementasi Algoritma Decision Tree untuk Klasifikasi Tingkat Kematangan Tomat",

        "algoritma": "Decision Tree",

        "fitur": "HSV (Hue, Saturation, Value)",

        "dataset": "200 Citra Tomat",

        "akurasi": "88%"

    }


    return render_template(
        "tentang.html",
        info=info
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )