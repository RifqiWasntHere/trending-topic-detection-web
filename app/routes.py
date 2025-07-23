from flask import Blueprint, render_template

router = Blueprint("routes", __name__, template_folder="templates")

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

# =========== API ROUTES (stripped down) ===========
@router.route("/api/data")
def api_data():
    return render_template("pages/api_template.html")

@router.route("/api/total_data_stats")
def total_data_stats():
    return render_template("pages/api_template.html")

@router.route("/api/preprocessing")
def api_data_preprocessing():
    return render_template("pages/api_template.html")

@router.route("/api/deleted_preprocessing_data", methods=['POST'])
def deleted_preprocessing_data():
    return render_template("pages/api_template.html")

@router.route("/api/checking_data_preprocessed", methods=['GET'])
def checking_data_preprocessed():
    return render_template("pages/api_template.html")

@router.route("/api/upload_csv", methods=['POST'])
def upload_csv_file():
    return render_template("pages/api_template.html")

# =========== UTILITY ROUTES (stripped down) ===========
@router.route("/run_preprocessing", methods=['POST'])
def run_preprocessing_route():
    return render_template("pages/api_template.html")

@router.route("/api/run_link_anomaly", methods=['POST'])
def run_link_anomaly():
    return render_template("pages/api_template.html")

@router.route("/api/run_lda", methods=['GET'])
def run_lda():
    return render_template("pages/api_template.html")

@router.route("/get_period_tweets", methods=['GET'])
def get_period_tweets():
    return render_template("pages/api_template.html")