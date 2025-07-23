import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import re
import pytz
from pathlib import Path
from datetime import datetime

# --- INIT GLOBAL VARIABLE ---
SLANGWORDS_DICT = None
STOPWORDS_SET = None
STEMMER = None

def init_preprocessing():
    global SLANGWORDS_DICT, STOPWORDS_SET, STEMMER
    if SLANGWORDS_DICT is None:
        slang_df = pd.read_csv('app/utils/data/slangwords.csv')
        SLANGWORDS_DICT = dict(zip(
            slang_df['tidak_baku'].str.lower().str.strip(),
            slang_df['baku'].str.lower().str.strip()
        ))
    if STOPWORDS_SET is None:
        STOPWORDS_SET = set(StopWordRemoverFactory().get_stop_words())
    if STEMMER is None:
        STEMMER = StemmerFactory().create_stemmer()

# Konversi UTC --> GMT +7 (Jakarta)
def convert_datetime(utc_time):
    try:
        if isinstance(utc_time, str):
            utc_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
        utc_tz = pytz.timezone("UTC")
        jakarta_tz = pytz.timezone("Asia/Jakarta")
        utc_dt = utc_tz.localize(utc_time) if utc_time.tzinfo is None else utc_time
        jakarta_dt = utc_dt.astimezone(jakarta_tz)
        return jakarta_dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return utc_time

# Case folding (meng-lowercase tweet)
def case_folding(text):
    return text.lower() if isinstance(text, str) else text

# Menghilangkan Link, Mention, Simbol
def cleansing(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'@\w+|#\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text) # Whitespace
    return text.strip()

def load_slangwords_dict(slangwords_path="app/utils/data/slangwords.csv"):
    slang_raw = pd.read_csv(slangwords_path)
    return dict(zip(
        slang_raw['tidak_baku'].str.lower().str.strip(),
        slang_raw['baku'].str.lower().str.strip()
    ))

def replace_slangwords(text, slangwords_dict):
    if not isinstance(text, str):
        return text
    words = text.split()
    replaced_words = [slangwords_dict.get(word.lower().strip(), word) for word in words]
    return ' '.join(replaced_words)

def load_stopwords():
    stop_factory = StopWordRemoverFactory()
    return set(word.lower() for word in stop_factory.get_stop_words())

def remove_stopwords(text, stopwords):
    if not isinstance(text, str):
        return text
    words = text.split()
    filtered_words = [word for word in words if word.lower().strip() not in stopwords]
    return ' '.join(filtered_words)

def create_stemmer():
    return StemmerFactory().create_stemmer()

def stemming(text, stemmer):
    if not isinstance(text, str):
        return text
    
    protected_words = {
        'ijazah', 'jokowi', 'presiden', 'universitas', 'ugm',
        'gadjah', 'mada', 'legalisir', 'dokumen', 'asli', 'palsu',
        'foto', 'scan', 'rektor', 'akademik', 'mahasiswa',
        'tanda', 'tangan', 'kampus', 'gelar', 'sidang', 'plagiarisme',
        'berkas', 'sertifikat', 'verifikasi', 'pengadilan', 'gugatan'
    }

    words = text.split()
    stemmed_words = [word if word in protected_words else stemmer.stem(word) for word in words]
    return ' '.join(stemmed_words)

# Mengekstrak user yang di mention, dan jumlah mention pada tweet
# def mentions_info(text):
#     text = text or ''
#     mentions = ','.join(re.findall(r'@\w+', text))
#     jumlah_mention = len(re.findall(r'@\w+', text))
#     return mentions, jumlah_mention
def mentions_info(text):
    if not text:
        return None, 0
    mention_list = re.findall(r'@\w+', text)
    mentions = ','.join(mention_list) if mention_list else None
    jumlah_mention = len(mention_list)
    return mentions, jumlah_mention

# Tokenisasi
def tokenize(text):
    if not isinstance(text, str):
        return []
    return text.split()

def preprocess_row(row, slangwords_dict, stopwords, stemmer):
    text = row['full_text']
    text = case_folding(text)
    text = cleansing(text)
    text = replace_slangwords(text, slangwords_dict)
    text = remove_stopwords(text, stopwords)
    text = stemming(text, stemmer)
    token = tokenize(text)
    created_at_jkt = convert_datetime(row['created_at'])
    mentions, jumlah_mention = mentions_info(row['full_text'])
    return pd.Series({
        'tweet_id_str': row['id_str'],
        'created_at': created_at_jkt,
        'processed_text': text,
        'token': token,
        'mentions': mentions,
        'jumlah_mention': jumlah_mention
    })