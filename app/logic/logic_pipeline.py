import pandas as pd
import numpy as np

from link_anomaly import (
    format_timestamps,
    hitung_probabilitas_mention_k,
    hitung_probabilitas_mention_user,
    hitung_skor_anomaly,
    hitung_skor_agregasi,
)
from sdnml import (
    sdnml,
    smooth_sdnml_scores,
    dynamic_threshold_optimization
)

def link_anomaly_pipeline(df: pd.DataFrame) -> dict:
    #-- Format timestamp
    df = format_timestamps(df)

    #-- Link Anomaly
    hasil_prob_k = hitung_probabilitas_mention_k(df)
    hasil_prob_user = hitung_probabilitas_mention_user(df, hasil_prob_k)
    hasil_skor_anom = hitung_skor_anomaly(hasil_prob_user)
    hasil_agregasi = hitung_skor_agregasi(hasil_skor_anom, 10)

    #-- SDNML Stage 1
    sdnml_first = sdnml(hasil_agregasi, 5, 2, 1)
    sdnml_first_smoothed = smooth_sdnml_scores(sdnml_first)

    #-- SDNML Stage 2
    sdnml_second = sdnml(sdnml_first_smoothed, 5, 2, 2)
    sdnml_second_smoothed = smooth_sdnml_scores(sdnml_second)

    #-- DTO
    final_scores = [row["smoothed_score"] for row in sdnml_second_smoothed]
    if final_scores:
        # bins_mean = np.mean(final_scores)
        # bins_std = np.std(final_scores)
        a, b = float(np.min(final_scores)), float(np.max(final_scores))
        dto_results = dynamic_threshold_optimization(sdnml_second_smoothed, 20, 0.1, 0.01, 0.1, a, b)
    else:
        dto_results = []

    return {
        "probabilitas_mention": [row['probabilitas_mention'] for row in hasil_prob_k],
        "probabilitas_user": [row.get('probabilitas_user', []) for row in hasil_prob_user],
        "skor_anomaly": [row.get('skor_anomaly', 0.0) for row in hasil_prob_user],
        "mentions": [row.get('mentions', []) for row in hasil_prob_k],
        "hasil_agregasi": hasil_agregasi,  
        "sdnml": sdnml_first,
        "sdnml_first_smoothed_stage": sdnml_first_smoothed,
        "sdnml_second_stage": sdnml_second,
        "sdnml_second_smoothed_stage": sdnml_second_smoothed,
        "dto_results": dto_results,

    }

#--# test #--#
df = pd.read_csv("tweets_ijazah_preprocessed.csv")
result = link_anomaly_pipeline(df)

dto_result = result["dto_results"]

for i in dto_result:
    print(i)