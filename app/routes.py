import math
from flask_socketio import emit
import time
from flask import Blueprint, render_template, request, jsonify
from app.utils.socketio import socketio
import pandas as pd
import os


from app.utils.preprocessing import create_stemmer, load_slangwords_dict, load_stopwords, preprocess_row

router = Blueprint("routes", __name__, template_folder="templates")

@router.route('/emit')
def emit():
    socketio.emit('notif', {'foo': 'bar'})
    return 'ok'

@router.route("/")
def home_route():
    return render_template("pages/index.html")

@router.route('/run_link_anomaly')
def link_anomaly_route():
    return render_template("pages/link_anomaly.html")

@router.route("/anomaly/preprocessing")
def preprocessing_route():
    return render_template("pages/preprocessing.html")

@router.route("/import")
def page_import_data():
    return render_template("pages/import.html")

@router.route("/topic_modeling")
def topic_modeling_route():
    return render_template("pages/modeling.html")

@router.route('/pengujian')
def pengujian_route():
    return render_template('pages/pengujian.html')


# ===================================================================== #
UPLOAD_DIR = "tmp"
UPLOAD_PATH = os.path.join(UPLOAD_DIR, "raw_dataset.csv")

@router.route("/api/upload_csv", methods=["POST"])
def api_upload_csv():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    file = request.files.get('fileInput')
    if not file:
        return jsonify({"success": False, "error": "No file uploaded."}), 400
    try:
        # Cek dan hapus file lama
        if os.path.exists(UPLOAD_PATH):
            os.remove(UPLOAD_PATH)
        # Simpan file baru
        df = pd.read_csv(file)
        df.to_csv(UPLOAD_PATH, index=False)
        return jsonify({"success": True, "message": "File uploaded."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@router.route("/api/data")
def api_data():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    if not os.path.exists(UPLOAD_PATH):
        # File belum ada
        return jsonify({
            "data": [],
            "total_count": 0,
            "page": 1,
            "total_pages": 1
        })

    df = pd.read_csv(UPLOAD_PATH)
    total_count = len(df)
    total_pages = max(1, math.ceil(total_count / per_page))
    start = (page-1) * per_page
    finish = start + per_page
    # Pastikan column-name yang benar
    # Mapping data frontend:{conversation_id_str, username, created_at, full_text}
    rows = []
    for _, row in df.iloc[start:finish].iterrows():
        rows.append({
            "conversation_id_str": row.get("id_str", ""),
            "created_at": row.get("created_at", ""),
            "full_text": row.get("full_text", ""),
        })
    return jsonify({
        "data": rows,
        "total_count": total_count,
        "page": page,
        "total_pages": total_pages
    })

@router.route("/api/delete_all", methods=["POST"])
def delete_all():
    if os.path.exists(UPLOAD_PATH):
        os.remove(UPLOAD_PATH)
    return jsonify({"success": True})

# =========== API ROUTES (stripped down) ===========

@router.route("/api/total_data_stats")
def total_data_stats():
    return render_template("pages/api_template.html")

# Inisiasi resource statis saat module import (cepat, satu kali)
slangwords_dict = load_slangwords_dict("app/utils/data/slangwords.csv")
stopwords = load_stopwords()
stemmer = create_stemmer()

@router.route("/preprocessing/run", methods=["POST"])
def run_preprocessing_route():
    import pandas as pd

    try:
        df = pd.read_csv("tmp/raw_dataset.csv")
        total = len(df)

        processed_rows = []
        start_time = time.time()

        for idx, (_, row) in enumerate(df.iterrows(), 1):  # 1-based
            hasil_row = preprocess_row(
                row,
                slangwords_dict=slangwords_dict,
                stopwords=stopwords,
                stemmer=stemmer
            )
            processed_rows.append(hasil_row)

            if idx % 10 == 0 or idx == total:
                elapsed = time.time() - start_time
                eta = (elapsed / idx) * (total - idx) if idx > 0 else 0
                socketio.emit(
                    'progress_cleansing_stemming',
                    {
                        'current': idx,
                        'total': total,
                        'eta': "{:02}:{:02}:{:02}".format(
                            int(eta // 3600), int((eta % 3600) // 60), int(eta % 60)
                        ),
                    },
                )

        result_df = pd.DataFrame(processed_rows)
        result_df['id'] = result_df['tweet_id_str']
        result_df.to_csv('tmp/preprocessed.csv', index=False)

        socketio.emit("progress_complete")  # Notifikasi selesai

        return jsonify({"status": "finished"})

    except Exception as e:
        socketio.emit("progress_error")
        return jsonify({"error": str(e)}), 500

@router.route("/api/preprocessing", methods=["GET"])
def api_preprocessing():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    try:
        df = pd.read_csv('tmp/preprocessed.csv')
    except:
        # Kalau belum pernah preprocessing
        return jsonify({
            "data": [],
            "total_count": 0,
            "page": 1,
            "total_pages": 1
        })

    total_count = len(df)
    total_pages = max(1, math.ceil(total_count / per_page))
    start = (page-1)*per_page
    end = start + per_page
    data_subset = df.iloc[start:end].to_dict(orient='records')

    # Pastikan kolomnya sesuai TABEL html: id, created_at, username, processed_text, jumlah_mention, mentions
    return jsonify({
        "data": data_subset,
        "total_count": total_count,
        "page": page,
        "total_pages": total_pages
    })

@router.route("/preprocessing/delete", methods=["POST"])
def deleted_preprocessing_data():
    import os
    try:
        os.remove("tmp/preprocessed.csv")
        # atau hapus tabel database
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@router.route("/preprocessing/check", methods=["GET"])
def checking_data_preprocessed():
    import os
    exists = os.path.isfile('tmp/preprocessed.csv')
    return jsonify({"exists": exists})

# =========== UTILITY router (stripped down) ===========

@router.route("/api/run_link_anomaly", methods=['POST'])
def run_link_anomaly():
    return render_template("pages/api_template.html")

@router.route("/api/run_lda", methods=['GET'])
def run_lda():
    return render_template("pages/api_template.html")

@router.route("/get_period_tweets", methods=['GET'])
def get_period_tweets():
    return render_template("pages/api_template.html")