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
    insert_history,
    insert_monitoring,
    get_monitoring,
    delete_monitoring
)


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = "tomato-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database.db"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model.pkl"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# DATABASE
# ============================================================

create_table()


# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(MODEL_PATH)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}


# ============================================================
# HELPER
# ============================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# EXTRACT HSV
# ============================================================

def extract_hsv(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Gambar tidak dapat dibaca.")

    image = cv2.resize(
        image,
        (224, 224)
    )

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    h = np.mean(
        hsv[:, :, 0]
    )

    s = np.mean(
        hsv[:, :, 1]
    )

    v = np.mean(
        hsv[:, :, 2]
    )

    return h, s, v


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(image_path):

    h, s, v = extract_hsv(
        image_path
    )

    feature = np.array([
        [h, s, v]
    ])

    prediction = model.predict(
        feature
    )[0]

    probability = model.predict_proba(
        feature
    )

    confidence = (
        np.max(probability)
        * 100
    )

    return (
        prediction,
        confidence,
        h,
        s,
        v
    )


# ============================================================
# NORMALIZE STATUS
# ============================================================

def normalize_prediction(prediction):

    prediction = str(
        prediction
    ).strip().lower()

    if prediction in [
        "matang",
        "mature",
        "ripe"
    ]:
        return "Matang"

    return "Mentah"


# ============================================================
# OTOMATIS STATUS MONITORING
# ============================================================

def calculate_monitoring_status(
    status_awal,
    lama_hari
):
    """
    Status berubah otomatis berdasarkan
    lama penyimpanan.

    Tetapi status awal tetap mengikuti
    hasil klasifikasi.

    Matang:
        Hari 1-2  -> Matang
        Hari 3-4  -> Busuk
        Hari >=5  -> Busuk

    Mentah:
        Hari 1-2  -> Mentah
        Hari 3-4  -> Setengah Matang
        Hari 5-7  -> Matang
        Hari >=8  -> Busuk
    """

    status_awal = str(
        status_awal
    ).strip().lower()

    # ========================================================
    # JIKA AWAL MATANG
    # ========================================================

    if status_awal == "matang":

        if lama_hari <= 2:
            return "Matang"

        return "Busuk"

    # ========================================================
    # JIKA AWAL MENTAH
    # ========================================================

    if status_awal == "mentah":

        if lama_hari <= 2:
            return "Mentah"

        elif lama_hari <= 4:
            return "Setengah Matang"

        elif lama_hari <= 7:
            return "Matang"

        else:
            return "Busuk"

    return "Mentah"


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM history
    """)

    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM history
        WHERE LOWER(prediction) = 'matang'
    """)

    matang = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM history
        WHERE LOWER(prediction) = 'mentah'
    """)

    mentah = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total=total,
        matang=matang,
        mentah=mentah
    )


# ============================================================
# DATASET
# ============================================================

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

    if os.path.exists(
        matang_folder
    ):
        matang = os.listdir(
            matang_folder
        )

    if os.path.exists(
        mentah_folder
    ):
        mentah = os.listdir(
            mentah_folder
        )

    return render_template(
        "dataset.html",
        matang=matang,
        mentah=mentah,
        total=len(matang) + len(mentah)
    )


# ============================================================
# EVALUASI
# ============================================================

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


# ============================================================
# KLASIFIKASI
# ============================================================

@app.route(
    "/klasifikasi",
    methods=["GET", "POST"]
)
def klasifikasi():

    if request.method == "POST":

        # ====================================================
        # CEK FILE
        # ====================================================

        if "image" not in request.files:

            flash(
                "Silakan pilih gambar terlebih dahulu.",
                "danger"
            )

            return redirect(
                request.url
            )

        file = request.files["image"]

        if file.filename == "":

            flash(
                "File belum dipilih.",
                "warning"
            )

            return redirect(
                request.url
            )

        if not allowed_file(
            file.filename
        ):

            flash(
                "Format file harus JPG, JPEG, atau PNG.",
                "danger"
            )

            return redirect(
                request.url
            )

        # ====================================================
        # SAVE IMAGE
        # ====================================================

        filename = secure_filename(
            file.filename
        )

        ext = filename.rsplit(
            ".",
            1
        )[1].lower()

        new_name = (
            f"{uuid.uuid4().hex}.{ext}"
        )

        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            new_name
        )

        file.save(
            save_path
        )

        # ====================================================
        # CLASSIFICATION
        # ====================================================

        start = datetime.now()

        try:

            (
                prediction,
                confidence,
                h,
                s,
                v
            ) = classify(
                save_path
            )

        except Exception as e:

            if os.path.exists(
                save_path
            ):
                os.remove(
                    save_path
                )

            flash(
                f"Gagal melakukan klasifikasi: {e}",
                "danger"
            )

            return redirect(
                request.url
            )

        finish = datetime.now()

        process_time = (
            finish - start
        ).total_seconds()

        # ====================================================
        # NORMALIZE PREDICTION
        # ====================================================

        prediction_normalized = (
            normalize_prediction(
                prediction
            )
        )

        # ====================================================
        # SIMPAN RIWAYAT
        # ====================================================

        insert_history(

            filename=new_name,

            h=round(h, 2),

            s=round(s, 2),

            v=round(v, 2),

            prediction=(
                prediction_normalized
            ),

            confidence=round(
                confidence,
                2
            ),

            process_time=round(
                process_time,
                4
            )
        )

        # ====================================================
        # OTOMATIS MASUK MONITORING
        # ====================================================

        tanggal_mulai = (
            datetime.now()
            .strftime("%Y-%m-%d")
        )

        # Status pertama mengikuti
        # hasil klasifikasi.

        status_awal = (
            prediction_normalized
        )

        insert_monitoring(

            nama_tomat=new_name,

            filename=new_name,

            tanggal_mulai=tanggal_mulai,

            status=status_awal,

            tanggal_busuk=None,

            keterangan=(
                "Monitoring otomatis "
                "dari hasil klasifikasi."
            )
        )

        # ====================================================
        # HASIL KLASIFIKASI
        # ====================================================

        return render_template(

            "klasifikasi.html",

            image=new_name,

            prediction=(
                prediction_normalized.upper()
            ),

            confidence=round(
                confidence,
                2
            ),

            hue=round(
                h,
                2
            ),

            saturation=round(
                s,
                2
            ),

            value=round(
                v,
                2
            ),

            process_time=round(
                process_time,
                4
            )
        )

    return render_template(
        "klasifikasi.html"
    )


# ============================================================
# RIWAYAT
# ============================================================

@app.route("/riwayat")
def riwayat():

    keyword = request.args.get(
        "search",
        ""
    ).strip()

    conn = sqlite3.connect(
        DATABASE_PATH
    )

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
        """, (
            f"%{keyword}%",
        ))

    data = cursor.fetchall()

    conn.close()

    return render_template(
        "riwayat.html",
        history=data,
        keyword=keyword
    )


# ============================================================
# MONITORING
# ============================================================

@app.route("/monitoring")
def monitoring():

    data = get_monitoring()

    today = datetime.now().date()

    monitoring_data = []

    for item in data:

        # ====================================================
        # TANGGAL MULAI
        # ====================================================

        try:

            tanggal_mulai = datetime.strptime(
                item["tanggal_mulai"],
                "%Y-%m-%d"
            ).date()

        except (
            ValueError,
            TypeError
        ):

            tanggal_mulai = today

        # ====================================================
        # HITUNG HARI
        # ====================================================

        lama_hari = (
            today - tanggal_mulai
        ).days + 1

        lama_hari = max(
            lama_hari,
            1
        )

        # ====================================================
        # STATUS AWAL
        # ====================================================

        status_awal = item["status"]

        # ====================================================
        # STATUS OTOMATIS
        # ====================================================

        status_sekarang = (
            calculate_monitoring_status(
                status_awal,
                lama_hari
            )
        )

        # ====================================================
        # TANGGAL BUSUK
        # ====================================================

        tanggal_busuk = (
            item["tanggal_busuk"]
        )

        if (
            status_sekarang == "Busuk"
            and
            not tanggal_busuk
        ):

            tanggal_busuk = (
                today.strftime(
                    "%Y-%m-%d"
                )
            )

            # Simpan tanggal busuk
            # ke database.

            conn = sqlite3.connect(
                DATABASE_PATH
            )

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE monitoring

                SET
                    tanggal_busuk = ?

                WHERE id = ?
            """, (
                tanggal_busuk,
                item["id"]
            ))

            conn.commit()
            conn.close()

        # ====================================================
        # DATA UNTUK TEMPLATE
        # ====================================================

        monitoring_data.append({

            "id": item["id"],

            "nama_tomat": item["nama_tomat"],

            "filename": item["filename"],

            "tanggal_mulai": item["tanggal_mulai"],

            "status": status_sekarang,

            "status_awal": status_awal,

            "tanggal_busuk": tanggal_busuk,

            "keterangan": item["keterangan"],

            "created_at": item["created_at"],

            "lama_penyimpanan": lama_hari
        })

    return render_template(
        "monitoring.html",
        monitoring=monitoring_data
    )


# ============================================================
# UPDATE STATUS MANUAL
# ============================================================

@app.route(
    "/monitoring/update/<int:id>",
    methods=["POST"]
)
def update_monitoring_data(id):

    status = request.form.get(
        "status"
    )

    keterangan = request.form.get(
        "keterangan",
        ""
    ).strip()

    allowed_status = [
        "Mentah",
        "Setengah Matang",
        "Matang",
        "Busuk"
    ]

    if status not in allowed_status:

        flash(
            "Status tidak valid.",
            "danger"
        )

        return redirect(
            url_for("monitoring")
        )

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute("""
        SELECT tanggal_busuk
        FROM monitoring
        WHERE id = ?
    """, (
        id,
    ))

    data = cursor.fetchone()

    if data is None:

        conn.close()

        flash(
            "Data monitoring tidak ditemukan.",
            "danger"
        )

        return redirect(
            url_for("monitoring")
        )

    tanggal_busuk = data[0]

    if (
        status == "Busuk"
        and
        tanggal_busuk is None
    ):

        tanggal_busuk = (
            datetime.now()
            .strftime("%Y-%m-%d")
        )

    elif status != "Busuk":

        tanggal_busuk = None

    cursor.execute("""
        UPDATE monitoring

        SET
            status = ?,
            tanggal_busuk = ?,
            keterangan = ?

        WHERE id = ?
    """, (
        status,
        tanggal_busuk,
        keterangan,
        id
    ))

    conn.commit()
    conn.close()

    flash(
        "Data monitoring berhasil diperbarui.",
        "success"
    )

    return redirect(
        url_for("monitoring")
    )


# ============================================================
# HAPUS MONITORING
# ============================================================

@app.route(
    "/monitoring/delete/<int:id>"
)
def delete_monitoring_data(id):

    delete_monitoring(
        id
    )

    flash(
        "Data monitoring berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("monitoring")
    )


# ============================================================
# HAPUS RIWAYAT
# ============================================================

@app.route(
    "/delete/<int:id>"
)
def delete(id):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM history
        WHERE id = ?
    """, (
        id,
    ))

    conn.commit()
    conn.close()

    flash(
        "Riwayat berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("riwayat")
    )


# ============================================================
# HAPUS SEMUA RIWAYAT
# ============================================================

@app.route(
    "/delete-all"
)
def delete_all():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM history
    """)

    conn.commit()
    conn.close()

    flash(
        "Semua riwayat berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("riwayat")
    )


# ============================================================
# TENTANG
# ============================================================

@app.route("/tentang")
def tentang():

    info = {

        "judul":
            "Implementasi Algoritma Decision Tree "
            "untuk Klasifikasi Tingkat Kematangan Tomat",

        "algoritma":
            "Decision Tree",

        "fitur":
            "HSV (Hue, Saturation, Value)",

        "dataset":
            "200 Citra Tomat",

        "akurasi":
            "88%"
    }

    return render_template(
        "tentang.html",
        info=info
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )