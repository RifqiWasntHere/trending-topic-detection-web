import numpy as np
import math
from typing import List, Dict

def sdnml(hasil_agregasi: List[float], m: int = 5, p: int = 2, layer: int = 1 ) -> List[Dict]:

    if layer == 1:
        s_x = [i['s_x'] for i in hasil_agregasi]
    elif layer == 2:
        s_x  =[i['smoothed_score'] for i in hasil_agregasi]

    skor_series = np.array(s_x)
    n = len(hasil_agregasi)
    V_t = np.identity(p)
    M_t = np.zeros((p,))
    diskrit_idx = range(len(s_x)) 

    ct_list, d_t, V_list, M_list, X_t, x_now_list, hasil_perhitungan = [], [], [], [], [], [], []

    for t in range(m + p, n):
        x_t = skor_series[t - p:t][::-1].reshape(-1, 1)
        x_now = skor_series[t]
        r = 1 / (t - m)
        V0 = np.identity(p)
        M0 = np.zeros(p)

        #-- Hitung Ct dan Dt
        c_t = r * (x_t.T @ V0 @ x_t)
        ct_list.append(c_t.item())
        d = c_t / (1 - r + c_t)
        d_t.append(d.item())

        #-- Hitung Mt dan Vt
        M_t = (1 - r) * M0 + r * (x_now * x_t.flatten())
        V_t = ((1 / (1 - r)) * V0) - ((r / (1 - r)) * (V0 @ x_t @ x_t.T @ V0)) / (1 - r + c_t)
        V_list.append(V_t.copy())
        M_list.append(M_t.copy())

        X_t.append(x_t)
        x_now_list.append(x_now)


    #-- Hitung At
    A_t = [V @ M for V, M in zip(V_list, M_list)]

    #-- Hitung residual (Et)
    e_t = [float(x_now_list[i] - np.dot(A_t[i], X_t[i])) for i in range(len(X_t))]

    #-- Hitung Tau t dan St
    tau_t = [
        float((1 / (i - m)) * sum([e_t[j]**2 for j in range(m+1, i+1)]))
        for i in range(m+1, len(e_t))
    ]
    s_t = [float((t - m) * tau) for t, tau in zip(range(m+1, len(e_t)), tau_t)]

    #-- Hitung K_t
    K_t = []
    for i in range(len(d_t)):
        t = m + i
        gamma_num_arg = (t + 1 - m - 1) / 2
        gamma_denom_arg = (t - m) / 2

        try:
            if gamma_num_arg <= 0 or gamma_denom_arg <= 0:
                K_t.append(float('nan'))
                continue
            gamma_num = math.gamma(gamma_num_arg)
            gamma_denom = math.gamma(gamma_denom_arg)
            numer = math.sqrt(math.pi) * gamma_num
            denom = (1 - d_t[i]) * gamma_denom
            Kt = numer / denom if denom != 0 else float('nan')
        except Exception:
            Kt = float('nan')
        K_t.append(Kt)

    #-- Hitung Density (PSDNML)
    p_sdnml = []
    for i in range(1, len(s_t)):
        try:
            a = (i - m) / 2
            b = (i - m - 1) / 2
            ps = (K_t[i]**(-1)) * (s_t[i]**(-a)) / (s_t[i-1]**(-b))
            p_sdnml.append(ps if ps > 1e-12 else 1e-10)
        except:
            p_sdnml.append(1e-10)

    #-- Hitung Skoring PSDNML
    score = [-float(np.log(p)) for p in p_sdnml]

    hasil_perhitungan = []
    for i in range(1, len(s_t)):
        idx_window = int(str(diskrit_idx[i]).split(',')[0])
        waktu_awal  = hasil_agregasi[idx_window]['waktu_awal']
        waktu_akhir = hasil_agregasi[idx_window]['waktu_akhir']

        hasil_perhitungan.append({
            "diskrit": diskrit_idx[i],
            "waktu_awal": waktu_awal,
            "waktu_akhir": waktu_akhir,
            "t": i + m + p,
            "e_t": e_t[i],
            "tau_t": tau_t[i],
            "s_t": s_t[i],
            "s_t_prev": s_t[i-1],
            "d_t": d_t[i],
            "K_t": K_t[i],
            "p_sdnml": p_sdnml[i-1],
            "score": score[i-1],
            "c_t": ct_list[i],
            "v_t": V_list[i],
            "m_t": M_list[i],
            "A_t": A_t[i]
        })
    return hasil_perhitungan

def smooth_sdnml_scores(results: List[Dict], window: int = 2) -> List[Dict]:
    smoothed = []
    for i in range(len(results) - window + 1):
        avg = np.mean([results[j]['score'] for j in range(i, i+window)])
        smoothed.append({
            "smoothed_score": avg,
            "waktu_awal": results[i]['waktu_awal'],
            "waktu_akhir": results[i+window-1]['waktu_akhir']
        })
    return smoothed

def dynamic_threshold_optimization( score_dicts, NH=20, rho=0.01, lambda_H=0.01, r_H=0.05, a=None, b=None ):
    scores = np.array([d['smoothed_score'] for d in score_dicts])
    M = len(scores)
    # Histogram bins setup
    if a is None: a = float(np.min(scores))
    if b is None: b = float(np.max(scores))
    bin_edges = [a] + [a + (b - a) / (NH - 2) * i for i in range(1, NH-1)] + [b]
    bins = np.array(bin_edges)
    q = np.ones(NH) / NH
    alarms = []
    thresholds = []

    output_alarm = []
    for j in range(M):
        cumsum_q = np.cumsum(q)
        l = np.argmax(cumsum_q >= 1 - rho)
        eta_j = a + (b - a) / (NH - 2) * (l + 1)
        thresholds.append(eta_j)
        alarm = int(scores[j] >= eta_j)
        alarms.append(alarm)

        output_alarm.append({
            'alarm': alarm,
            'score': scores[j],
            'threshold': eta_j,
            'waktu_awal': score_dicts[j]['waktu_awal'],
            'waktu_akhir': score_dicts[j]['waktu_akhir'],
        })
        #-- Histogram update
        h = np.searchsorted(bins, scores[j], side='right') - 1 
        h = max(0, min(h, NH-1))
        for idx in range(NH):
            if idx == h:
                q[idx] = (1 - r_H)*q[idx] + r_H
            else:
                q[idx] = (1 - r_H)*q[idx]
        q = (q + lambda_H) / (np.sum(q) + NH*lambda_H)
    
    return output_alarm  