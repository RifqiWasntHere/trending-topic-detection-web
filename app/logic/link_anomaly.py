from typing import List, Dict
from collections import Counter
from datetime import datetime, timedelta
import pandas as pd
import math

def format_timestamps(df: pd.DataFrame, time_col: str = 'created_at') -> pd.DataFrame:
    """Format kolom timestamp ke string ISO."""
    df = df.copy()
    if time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col], format="%a %b %d %H:%M:%S %z %Y", errors='coerce')
        df[time_col] = df[time_col].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def hitung_probabilitas_mention_k(tweets_df: pd.DataFrame) -> List[Dict]:
    alpha = 0.5
    beta = 0.5
    hasil_perhitungan = []
    tweets_df = tweets_df.copy()
    tweets_df['created_at'] = pd.to_datetime(tweets_df['created_at'])
    m = 0  # total mention sebelum tweet ke-i
    for i, row in tweets_df.iterrows():
        n = i
        k = row['jumlah_mention']
        probabilitas = 1.0
        for j in range(k + 1):
            if j == 0:
                probabilitas *= (n + alpha) / (m + k + beta)
            probabilitas *= (m + beta + j) / (n + m + alpha + beta + j)
        hasil_perhitungan.append({
            "tweet_id_str": row['tweet_id_str'],
            "created_at": row['created_at'],
            "probabilitas_mention": probabilitas,
            "mentions": k
        })
        m += k
    return hasil_perhitungan

def hitung_probabilitas_mention_user(
    tweets_df: pd.DataFrame, 
    hasil_perhitungan: List[Dict]
) -> List[Dict]:
    y = 0.5
    total_mention = 0
    mention_counter = Counter()
    tweets_df = tweets_df.copy()
    tweets_df['created_at'] = pd.to_datetime(tweets_df['created_at'])
    hasil_dict = {h['tweet_id_str']: h for h in hasil_perhitungan}
    for idx, row in tweets_df.iterrows():
        tweet_id = row['tweet_id_str']
        # Pastikan mentions_list berbentuk list of user
        if isinstance(row['mentions'], list):
            mentions_list = [str(m).strip() for m in row['mentions'] if str(m).strip()]
        elif isinstance(row['mentions'], str):
            mentions_list = [m.strip() for m in row['mentions'].split(',') if m.strip()]
        else:
            mentions_list = []
        pmention_list = []
        m = total_mention
        for mention in mentions_list:
            mv = mention_counter[mention]
            if m > 0:
                p = mv / (m + y) if mv > 0 else y / (m + y)
            else:
                p = 1.0
            pmention_list.append(p)
        # Update total and counter after processing
        total_mention += len(mentions_list)
        for mention in mentions_list:
            mention_counter[mention] += 1
        # Simpan hasil pada dict yang sudah ada (update field)
        if tweet_id in hasil_dict:
            hasil_dict[tweet_id]['probabilitas_user'] = pmention_list
        else:
            hasil_dict[tweet_id] = {
                'tweet_id_str': tweet_id,
                'probabilitas_user': pmention_list
            }
    return list(hasil_dict.values())

def hitung_skor_anomaly(hasil_perhitungan: List[Dict]) -> List[Dict]:
    for item in hasil_perhitungan:
        prob_mention = item.get("probabilitas_mention", 1e-10)
        prob_users = item.get("probabilitas_user", [])
        prob_mention = max(prob_mention, 1e-10)  # avoid log(0)
        prob_users = [max(p, 1e-10) for p in prob_users]
        user_log_sum = sum(math.log(p) for p in prob_users)
        skor_anomaly = -math.log(prob_mention) - user_log_sum
        item["skor_anomaly"] = skor_anomaly
    return hasil_perhitungan

def hitung_skor_agregasi(hasil_perhitungan: List[Dict], window_minutes: int = 10) -> List[Dict]:
    if not hasil_perhitungan:
        return []
    hasil = sorted(hasil_perhitungan, key=lambda x: x['created_at'])
    waktu_awal = hasil[0]['created_at']
    waktu_awal_dt = pd.to_datetime(waktu_awal)
    waktu_akhir_data = pd.to_datetime(hasil[-1]['created_at'])
    window_r = timedelta(minutes=window_minutes)
    hasil_agregasi = []
    diskrit_index = 1
    waktu_awal_cursor = waktu_awal_dt
    waktu_akhir_cursor = waktu_awal_cursor + window_r
    while waktu_awal_cursor <= waktu_akhir_data:
        skor_total = 0.0
        jumlah_mention_agregasi = 0
        for data in hasil:
            tweet_waktu = pd.to_datetime(data['created_at'])
            if waktu_awal_cursor <= tweet_waktu < waktu_akhir_cursor:
                skor_total += data.get('skor_anomaly', 0.0)
                jumlah_mention_agregasi += data.get('mentions', 0)
        s_x = skor_total / window_minutes
        hasil_agregasi.append({
            "diskrit": diskrit_index,
            "waktu_awal": waktu_awal_cursor.strftime("%Y-%m-%d %H:%M:%S"),
            "waktu_akhir": waktu_akhir_cursor.strftime("%Y-%m-%d %H:%M:%S"),
            "s_x": s_x,
            "jumlah_mention_agregasi": jumlah_mention_agregasi
        })
        waktu_awal_cursor = waktu_akhir_cursor
        waktu_akhir_cursor += window_r
        diskrit_index += 1
    return hasil_agregasi