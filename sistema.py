import streamlit as st
import streamlit.components.v1 as components
import requests
from itertools import combinations
from collections import Counter
import math
import time
import re
import json
import io
import traceback
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# CONFIGURAÇÃO DE PÁGINA (PRIMEIRO COMANDO STREAMLIT OBRIGATÓRIO)
# ==============================================================================
st.set_page_config(
    page_title="MEGA60 - Alto Contraste & Blindado",
    page_icon="🍀",
    layout="wide"
)

# ==============================================================================
# ENCAPSULAMENTO GLOBAL DE SEGURANÇA
# ==============================================================================
try:
    # ESTILIZAÇÃO CSS: FONTE MAIOR, TUDO PRETO E ALTO CONTRASTE (ZERO VERDE)
    st.markdown('''
    <style>
        html, body, [class*="css"], .stMarkdown, p, span, label, div, input, textarea, select {
            color: #000000 !important;
            font-weight: 800 !important;
            font-family: Arial, Helvetica, sans-serif !important;
        }
        
        h1 {
            font-size: 2.3rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }
        h2 {
            font-size: 1.9rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }
        h3 {
            font-size: 1.5rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }
        h4 {
            font-size: 1.25rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            color: #000000 !important;
            font-size: 1.1rem !important;
            font-weight: 900 !important;
        }

        .stButton > button {
            color: #000000 !important;
            font-size: 1.2rem !important;
            font-weight: 900 !important;
            border: 3px solid #000000 !important;
            background-color: #ffffff !important;
            border-radius: 8px !important;
            padding: 6px 4px !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #facc15 !important;
            color: #000000 !important;
            border: 3px solid #000000 !important;
        }

        button[data-baseweb="tab"] {
            font-size: 1.2rem !important;
            font-weight: 900 !important;
            color: #000000 !important;
        }

        .stSelectbox label, .stMultiSelect label, .stSlider label, .stTextInput label, .stTextArea label, .stNumberInput label {
            font-size: 1.15rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 2.0rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 1.15rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }

        .stAlert {
            background-color: #fef08a !important;
            border: 3px solid #000000 !important;
        }
        .stAlert p {
            font-size: 1.15rem !important;
            color: #000000 !important;
            font-weight: 900 !important;
        }
        
        code {
            color: #000000 !important;
            background-color: #fef08a !important;
            font-weight: 900 !important;
            font-size: 1.15rem !important;
            border: 2px solid #000000 !important;
            padding: 2px 6px !important;
        }
    </style>
    ''', unsafe_allow_html=True)

    # ==============================================================================
    # CONSTANTES E ESTRUTURA DA MATRIZ 6x10
    # ==============================================================================
    TOTAL_NUMS = 60
    TAMANHO_JOGO_FINAL = 6
    FIBONACCI_MEGASENA = {1, 2, 3, 5, 8, 13, 21, 34, 55}
    PRIMOS_MEGASENA = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}

    MOLDURA_SET = (
        set(range(1, 11)) |
        set(range(51, 61)) |
        {r * 10 + 1 for r in range(6)} |
        {r * 10 + 10 for r in range(6)}
    )

    DEZENAS_BASE_3010 = {5, 9, 16, 40, 41, 59}

    FALLBACK_MEGASENA = [
        [4, 12, 18, 30, 35, 54], [1, 9, 15, 23, 44, 52], [7, 14, 27, 39, 48, 59],
        [10, 11, 25, 33, 42, 58], [3, 16, 28, 37, 45, 60], [5, 20, 22, 34, 49, 56],
        [8, 17, 31, 40, 50, 57], [2, 13, 24, 38, 43, 55], [6, 19, 29, 36, 47, 53],
        [12, 21, 32, 41, 46, 51], [4, 15, 26, 35, 48, 58], [7, 18, 23, 39, 44, 59],
        [1, 10, 27, 34, 42, 54], [9, 14, 30, 37, 50, 60], [3, 16, 25, 38, 49, 57],
        [5, 11, 28, 33, 45, 53], [8, 20, 31, 43, 52, 56], [2, 17, 24, 36, 47, 55],
        [6, 13, 29, 40, 46, 51], [12, 19, 32, 41, 50, 58]
    ]

    PAR_LOOKUP = [False] + [(n % 2 == 0) for n in range(1, 61)]
    PRIMO_LOOKUP = [False] + [(n in PRIMOS_MEGASENA) for n in range(1, 61)]
    MOLDURA_LOOKUP = [False] + [(n in MOLDURA_SET) for n in range(1, 61)]
    ROW_LOOKUP = [0] + [(n - 1) // 10 for n in range(1, 61)]
    COL_LOOKUP = [0] + [(n - 1) % 10 for n in range(1, 61)]
    DC_LOOKUP = [0] + [(((n - 1) % 10) + ((n - 1) // 10)) % 10 for n in range(1, 61)]
    DD_LOOKUP = [0] + [(((n - 1) % 10) - ((n - 1) // 10)) % 10 for n in range(1, 61)]

    PROPS = {}
    for n in range(1, 61):
        PROPS[n] = {
            "r": ROW_LOOKUP[n],
            "c": COL_LOOKUP[n],
            "dc": DC_LOOKUP[n],
            "dd": DD_LOOKUP[n],
            "is_primo": PRIMO_LOOKUP[n],
            "is_par": PAR_LOOKUP[n],
            "is_moldura": MOLDURA_LOOKUP[n],
            "is_fib": n in FIBONACCI_MEGASENA
        }

    OPCOES_QUANTIDADE = {
        "Livre (0 a 6)": (0, 6),
        "0 (Nenhuma)": (0, 0),
        "Exatamente 1": (1, 1),
        "Exatamente 2": (2, 2),
        "Exatamente 3": (3, 3),
        "Exatamente 4": (4, 4),
        "0 ou 1": (0, 1),
        "1 ou 2": (1, 2),
        "0 a 2": (0, 2),
        "2 a 3": (2, 3),
        "1 a 3": (1, 3)
    }

    PRESETS_PADRAO = {
        "FILTRO3010": {
            "linhas": ["Exatamente 2", "Exatamente 1", "0 (Nenhuma)", "Exatamente 1", "Exatamente 1", "Exatamente 1"],
            "colunas": ["Exatamente 1", "0 (Nenhuma)", "0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 1", "Exatamente 1", "0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 2", "Exatamente 1"],
            "diag_cresc": ["0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 1", "Exatamente 1", "Exatamente 2", "0 (Nenhuma)", "Exatamente 1", "0 (Nenhuma)", "Exatamente 1", "0 (Nenhuma)"],
            "diag_decresc": ["0 (Nenhuma)", "0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 1", "Exatamente 2", "0 (Nenhuma)", "Exatamente 2", "0 (Nenhuma)", "Exatamente 1", "0 (Nenhuma)"],
            "primos": [3],
            "pares": ["2P / 4I"],
            "moldura": [5],
            "soma": (150, 190)
        },
        "FILTRO3010_DUPLAS (Gerador Aberto)": {
            "linhas": ["1 ou 2", "0 a 2", "0 a 2", "0 a 2", "0 a 2", "0 a 2"],
            "colunas": ["0 a 2"] * 10,
            "diag_cresc": ["0 a 2"] * 10,
            "diag_decresc": ["0 a 2"] * 10,
            "primos": [1, 2, 3],
            "pares": ["3P / 3I", "4P / 2I", "2P / 4I"],
            "moldura": [2, 3, 4, 5],
            "soma": (120, 245)
        },
        "MEGA60: 1 por Linha Padrão (6 Dezenas)": {
            "linhas": ["Exatamente 1"] * 6,
            "colunas": ["0 ou 1"] * 10,
            "diag_cresc": ["0 ou 1"] * 10,
            "diag_decresc": ["0 ou 1"] * 10,
            "primos": [1, 2],
            "pares": ["3P / 3I", "2P / 4I", "4P / 2I"],
            "moldura": [2, 3, 4],
            "soma": (110, 240)
        }
    }

    # ==============================================================================
    # MOTOR TÉRMICO DE ELLIOTT & SELEÇÃO DE ELITE
    # ==============================================================================
    def calcular_metricas_elliott(historico):
        total = len(historico)
        atrasos = {n: total for n in range(1, 61)}
        freq_5 = {n: 0 for n in range(1, 61)}
        freq_15 = {n: 0 for n in range(1, 61)}

        for idx_rev, sorteio in enumerate(reversed(historico)):
            for n in sorteio:
                if atrasos[n] == total:
                    atrasos[n] = idx_rev
                if idx_rev < 5:
                    freq_5[n] += 1
                if idx_rev < 15:
                    freq_15[n] += 1

        dados = {}
        for n in range(1, 61):
            atr = atrasos[n]
            dist_fib = min(abs(atr - f) for f in [1, 2, 3, 5, 8, 13, 21])
            score_retracao = max(0.0, 10.0 - (dist_fib * 2.2))
            score_impulso = (freq_5[n] * 6.5) + (freq_15[n] * 2.5)
            score_fib = 3.5 if PROPS[n]["is_fib"] else 0.0
            penalidade = -4.0 if atr > 21 else 0.0

            score_total = max(0.0, score_retracao + score_impulso + score_fib + penalidade)
            dados[n] = {
                "numero": n,
                "score": round(score_total, 1),
                "atraso": atr,
                "is_fib": PROPS[n]["is_fib"],
                "is_primo": PROPS[n]["is_primo"],
                "is_par": PROPS[n]["is_par"],
                "dc": PROPS[n]["dc"],
                "dd": PROPS[n]["dd"]
            }

        return dados

    def extrair_analise_elite(dados_calor):
        ranking = sorted(dados_calor.values(), key=lambda x: x["score"], reverse=True)
        
        melhores_primos = [x["numero"] for x in ranking if x["is_primo"]][:5]
        melhores_pares = [x["numero"] for x in ranking if x["is_par"]][:3]
        melhores_impares = [x["numero"] for x in ranking if not x["is_par"]][:5]
        
        dc_scores = {d: 0.0 for d in range(10)}
        dd_scores = {d: 0.0 for d in range(10)}
        for n, val in dados_calor.items():
            dc_scores[val["dc"]] += val["score"]
            dd_scores[val["dd"]] += val["score"]
            
        melhores_dc = sorted(dc_scores.keys(), key=lambda d: dc_scores[d], reverse=True)[:3]
        melhores_dd = sorted(dd_scores.keys(), key=lambda d: dd_scores[d], reverse=True)[:3]
        
        pool_elite = sorted(list(set(melhores_primos) | set(melhores_pares) | set(melhores_impares)))
        
        return {
            "primos": melhores_primos,
            "pares": melhores_pares,
            "impares": melhores_impares,
            "dc": melhores_dc,
            "dd": melhores_dd,
            "pool_elite": pool_elite
        }
