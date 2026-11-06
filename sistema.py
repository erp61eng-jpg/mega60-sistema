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

# ESTILIZAÇÃO CSS GLOBAL
st.markdown('''
<style>
    html, body, [class*="css"], .stMarkdown, p, span, label, div, input, textarea, select {
        color: #000000 !important;
        font-weight: 800 !important;
        font-family: Arial, Helvetica, sans-serif !important;
        line-height: 1.5 !important;
    }
    h1, h2, h3, h4 { color: #000000 !important; font-weight: 900 !important; }
    .stButton > button {
        color: #000000 !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        border: 3px solid #000000 !important;
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #facc15 !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
    }
</style>
''', unsafe_allow_html=True)


# ==============================================================================
# ==============================================================================
# 🛠️ ETAPA 1: CONSTANTES, LOOKUPS, FUNÇÕES AUXILIARES E MOTORES DE CÁLCULO
# ==============================================================================
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
        "r": ROW_LOOKUP[n], "c": COL_LOOKUP[n], "dc": DC_LOOKUP[n], "dd": DD_LOOKUP[n],
        "is_primo": PRIMO_LOOKUP[n], "is_par": PAR_LOOKUP[n], "is_moldura": MOLDURA_LOOKUP[n],
        "is_fib": n in FIBONACCI_MEGASENA
    }

OPCOES_QUANTIDADE = {
    "Livre (0 a 6)": (0, 6), "0 (Nenhuma)": (0, 0), "Exatamente 1": (1, 1),
    "Exatamente 2": (2, 2), "Exatamente 3": (3, 3), "Exatamente 4": (4, 4),
    "0 ou 1": (0, 1), "1 ou 2": (1, 2), "0 a 2": (0, 2), "2 a 3": (2, 3), "1 a 3": (1, 3)
}

PRESETS_PADRAO = {
    "FILTRO3010": {
        "linhas": ["Exatamente 2", "Exatamente 1", "0 (Nenhuma)", "Exatamente 1", "Exatamente 1", "Exatamente 1"],
        "colunas": ["Exatamente 1", "0 (Nenhuma)", "0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 1", "Exatamente 1", "0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 2", "Exatamente 1"],
        "diag_cresc": ["0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 1", "Exatamente 1", "Exatamente 2", "0 (Nenhuma)", "Exatamente 1", "0 (Nenhuma)", "Exatamente 1", "0 (Nenhuma)"],
        "diag_decresc": ["0 (Nenhuma)", "0 (Nenhuma)", "0 (Nenhuma)", "Exatamente 1", "Exatamente 2", "0 (Nenhuma)", "Exatamente 2", "0 (Nenhuma)", "Exatamente 1", "0 (Nenhuma)"],
        "primos": [3], "pares": ["2P / 4I"], "moldura": [5], "soma": (150, 190)
    }
}

def calcular_metricas_elliott(historico):
    total = len(historico)
    atrasos = {n: total for n in range(1, 61)}
    freq_5, freq_15 = {n: 0 for n in range(1, 61)}, {n: 0 for n in range(1, 61)}
    for idx_rev, sorteio in enumerate(reversed(historico)):
        for n in sorteio:
            if atrasos[n] == total: atrasos[n] = idx_rev
            if idx_rev < 5: freq_5[n] += 1
            if idx_rev < 15: freq_15[n] += 1
    dados = {}
    for n in range(1, 61):
        atr = atrasos[n]
        dist_fib = min(abs(atr - f) for f in [1, 2, 3, 5, 8, 13, 21])
        score_retracao = max(0.0, 10.0 - (dist_fib * 2.2))
        score_impulso = (freq_5[n] * 6.5) + (freq_15[n] * 2.5)
        score_fib = 3.5 if PROPS[n]["is_fib"] else 0.0
        penalidade = -4.0 if atr > 21 else 0.0
        score_total = max(0.0, score_retracao + score_impulso + score_fib + penalidade)
        dados[n] = {"numero": n, "score": round(score_total, 1), "atraso": atr, "is_fib": PROPS[n]["is_fib"], "is_primo": PROPS[n]["is_primo"], "is_par": PROPS[n]["is_par"], "dc": PROPS[n]["dc"], "dd": PROPS[n]["dd"]}
    return dados

def extrair_analise_elite(dados_calor):
    ranking = sorted(dados_calor.values(), key=lambda x: x["score"], reverse=True)
    melhores_primos = [x["numero"] for x in ranking if x["is_primo"]][:5]
    melhores_pares = [x["numero"] for x in ranking if x["is_par"]][:3]
    melhores_impares = [x["numero"] for x in ranking if not x["is_par"]][:5]
    dc_scores, dd_scores = {d: 0.0 for d in range(10)}, {d: 0.0 for d in range(10)}
    for n, val in dados_calor.items():
        dc_scores[val["dc"]] += val["score"]
        dd_scores[val["dd"]] += val["score"]
    melhores_dc = sorted(dc_scores.keys(), key=lambda d: dc_scores[d], reverse=True)[:3]
    melhores_dd = sorted(dd_scores.keys(), key=lambda d: dd_scores[d], reverse=True)[:3]
    pool_elite = sorted(list(set(melhores_primos) | set(melhores_pares) | set(melhores_impares)))
    return {"primos": melhores_primos, "pares": melhores_pares, "impares": melhores_impares, "dc": melhores_dc, "dd": melhores_dd, "pool_elite": pool_elite}

def mapear_quantidade_para_rotulo(qtd, modo="exato"):
    if modo == "exato":
        mapa = {0: "0 (Nenhuma)", 1: "Exatamente 1", 2: "Exatamente 2", 3: "Exatamente 3", 4: "Exatamente 4"}
        return mapa.get(qtd, "Livre (0 a 6)")
    return "0 a 2" if qtd <= 2 else "Livre (0 a 6)"

def mapear_intervalo_para_opcao(min_v, max_v, flexivel=False):
    if flexivel:
        min_v = max(0, min_v - 1)
        max_v = min(6, max_v + 1)
    for label, (low, high) in OPCOES_QUANTIDADE.items():
        if low == min_v and high == max_v: return label
    return "Livre (0 a 6)"

def extrair_filtros_de_jogo(dezenas, modo="exato", margem_soma=25):
    dezenas = sorted(list(set(dezenas)))
    total_dezenas = len(dezenas)
    if not (6 <= total_dezenas <= 60): return None
    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*6, [0]*10, [0]*10, [0]*10
    for n in dezenas:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1
    pares_total = sum(1 for n in dezenas if PAR_LOOKUP[n])
    primos_total = sum(1 for n in dezenas if PRIMO_LOOKUP[n])
    moldura_total = sum(1 for n in dezenas if MOLDURA_LOOKUP[n])
    soma_total = sum(dezenas)
    return {
        "linhas": [mapear_quantidade_para_rotulo(q, "exato") for q in l_cnt],
        "colunas": [mapear_quantidade_para_rotulo(q, "exato") for q in c_cnt],
        "diag_cresc": [mapear_quantidade_para_rotulo(q, "exato") for q in dc_cnt],
        "diag_decresc": [mapear_quantidade_para_rotulo(q, "exato") for q in dd_cnt],
        "primos": [primos_total], "pares": [f"{pares_total}P / {6 - pares_total}I"],
        "moldura": [moldura_total], "soma": (max(50, soma_total - margem_soma), min(320, soma_total + margem_soma))
    }

def extrair_filtros_multiconcursos(lista_sorteios, modo="preciso"):
    if not lista_sorteios: return None
    is_flex = modo == "flexivel"
    min_l, max_l = [99] * 6, [-1] * 6
    min_c, max_c = [99] * 10, [-1] * 10
    min_dc, max_dc = [99] * 10, [-1] * 10
    min_dd, max_dd = [99] * 10, [-1] * 10
    conjunto_primos, conjunto_pares, conjunto_moldura, somas_obs = set(), set(), set(), []
    for sorteio in lista_sorteios:
        dezenas = sorted(sorteio)
        l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*6, [0]*10, [0]*10, [0]*10
        for n in dezenas:
            l_cnt[ROW_LOOKUP[n]] += 1
            c_cnt[COL_LOOKUP[n]] += 1
            dc_cnt[DC_LOOKUP[n]] += 1
            dd_cnt[DD_LOOKUP[n]] += 1
        for r in range(6):
            min_l[r], max_l[r] = min(min_l[r], l_cnt[r]), max(max_l[r], l_cnt[r])
        for c in range(10):
            min_c[c], max_c[c] = min(min_c[c], c_cnt[c]), max(max_c[c], c_cnt[c])
        for d in range(10):
            min_dc[d], max_dc[d] = min(min_dc[d], dc_cnt[d]), max(max_dc[d], dc_cnt[d])
            min_dd[d], max_dd[d] = min(min_dd[d], dd_cnt[d]), max(max_dd[d], dd_cnt[d])
        conjunto_primos.add(sum(1 for n in dezenas if PRIMO_LOOKUP[n]))
        pa = sum(1 for n in dezenas if PAR_LOOKUP[n])
        conjunto_pares.add(f"{pa}P / {6 - pa}I")
        conjunto_moldura.add(sum(1 for n in dezenas if MOLDURA_LOOKUP[n]))
        somas_obs.append(sum(dezenas))
    return {
        "linhas": [mapear_intervalo_para_opcao(min_l[r], max_l[r], is_flex) for r in range(6)],
        "colunas": [mapear_intervalo_para_opcao(min_c[c], max_c[c], is_flex) for c in range(10)],
        "diag_cresc": [mapear_intervalo_para_opcao(min_dc[d], max_dc[d], is_flex) for d in range(10)],
        "diag_decresc": [mapear_intervalo_para_opcao(min_dd[d], max_dd[d], is_flex) for d in range(10)],
        "primos": sorted(list(conjunto_primos)), "pares": sorted(list(conjunto_pares)),
        "moldura": sorted(list(conjunto_moldura)), "soma": (max(50, min(somas_obs)-20), min(320, max(somas_obs)+20))
    }

def validar_aposta_final_6(jogo, cfg):
    soma_j = sum(jogo)
    if not (cfg["faixa_soma"][0] <= soma_j <= cfg["faixa_soma"][1]): return False
    if sum(1 for n in jogo if PAR_LOOKUP[n]) not in cfg["pares_aceitos"]: return False
    if sum(1 for n in jogo if PRIMO_LOOKUP[n]) not in cfg["primos_aceitos"]: return False
    if sum(1 for n in jogo if MOLDURA_LOOKUP[n]) not in cfg["moldura_aceita"]: return False
    l_cnt, c_cnt, dc_cnt, dd_cnt = [0]*6, [0]*10, [0]*10, [0]*10
    for n in jogo:
        l_cnt[ROW_LOOKUP[n]] += 1
        c_cnt[COL_LOOKUP[n]] += 1
        dc_cnt[DC_LOOKUP[n]] += 1
        dd_cnt[DD_LOOKUP[n]] += 1
    for r in range(6):
        if not (cfg["linhas"][r][0] <= l_cnt[r] <= cfg["linhas"][r][1]): return False
    for c in range(10):
        if not (cfg["colunas"][c][0] <= c_cnt[c] <= cfg["colunas"][c][1]): return False
    for d in range(10):
        if not (cfg["diag_cresc"][d][0] <= dc_cnt[d] <= cfg["diag_cresc"][d][1]): return False
        if not (cfg["diag_decresc"][d][0] <= dd_cnt[d] <= cfg["diag_decresc"][d][1]): return False
    return True

def executar_varredura_pool(pool_dezenas, cfg, bar_progresso, ticker_metricas, teto_max=None):
    t_inicio = time.time()
    dezenas_candidatas = sorted(list(pool_dezenas))
    if len(dezenas_candidatas) < 6: return []
    total_combinacoes = math.comb(len(dezenas_candidatas), 6)
    jogos_aprovados = []
    testadas = 0
    t_ultimo_update = 0.0
    for comb in combinations(dezenas_candidatas, 6):
        testadas += 1
        if validar_aposta_final_6(comb, cfg):
            jogos_aprovados.append(sorted(list(comb)))
            if teto_max is not None and len(jogos_aprovados) >= teto_max: break
        t_agora = time.time()
        if t_agora - t_ultimo_update >= 0.25:
            t_ultimo_update = t_agora
            prog = min(1.0, testadas / total_combinacoes)
            bar_progresso.progress(prog)
            ticker_metricas.markdown(f"**Processando:** `{testadas:,}` de `{total_combinacoes:,}` ({prog*100:.1f}%) | Aprovadas: `{len(jogos_aprovados):,}`")
    bar_progresso.progress(1.0)
    return jogos_aprovados

def processar_arquivo_upload(conteudo_bytes):
    texto = conteudo_bytes.decode("utf-8", errors="ignore")
    linhas = texto.strip().splitlines()
    jogos, invalidos = [], 0
    for linha in linhas:
        l = linha.strip()
        if not l: continue
        nums = [int(x) for x in re.findall(r"\b\d+\b", l)]
        nums_validos = sorted(list(set([n for n in nums if 1 <= n <= 60])))
        if len(nums_validos) == 6: jogos.append(nums_validos)
        else: invalidos += 1
    return jogos, invalidos

def conferir_apostas_contra_sorteio(lista_jogos, dezenas_sorteadas):
    sorteio_set = set(dezenas_sorteadas)
    placar = {6: [], 5: [], 4: [], 3: [], 2: [], 1: [], 0: []}
    relatorio = []
    for idx, jogo in enumerate(lista_jogos):
        acertos = sorted(list(set(jogo) & sorteio_set))
        qtd = len(acertos)
        placar[qtd].append(idx + 1)
        relatorio.append({
            "num_aposta": idx + 1,
            "jogo": sorted(jogo),
            "qtd_acertos": qtd,
            "acertos": acertos
        })
    return relatorio, placar

def render_html_seguro(conteudo_html, altura=380):
    try:
        if hasattr(st, "html"): st.html(conteudo_html)
        else: components.html(conteudo_html, height=altura, scrolling=False)
    except Exception:
        components.html(conteudo_html, height=altura, scrolling=False)

def render_cartao_sorteio_html(dezenas, titulo="CARTÃO OFICIAL DO SORTEIO"):
    bolas_html = "".join([f"<span style='display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;background:#facc15;color:#000000;font-weight:900;font-size:22px;border-radius:50%;margin:0 6px;border:3px solid #000000;font-family:monospace;'>{n:02d}</span>" for n in dezenas])
    st.markdown(f'''<div style="background:#ffffff;border:4px solid #000000;border-radius:12px;padding:16px;margin:12px 0;text-align:center;"><div style="font-weight:900;color:#000000;font-size:18px;margin-bottom:10px;text-transform:uppercase;">🏆 {titulo}</div><div style="display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:8px;">{bolas_html}</div></div>''', unsafe_allow_html=True)

def render_volante_conferencia(jogo, dezenas_sorteio, titulo=""):
    jogo_set, sorteio_set = set(jogo), set(dezenas_sorteio)
    celulas = ""
    for r in range(6):
        for c in range(10):
            n = r * 10 + c + 1
            if n in jogo_set and n in sorteio_set: celulas += f'<div style="width:42px;height:42px;background:#facc15;color:#000000;font-weight:900;border:3px solid #000000;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:monospace;font-size:15px;">{n:02d}<span style="font-size:11px;line-height:8px;font-weight:900;">★</span></div>'
            elif n in jogo_set: celulas += f'<div style="width:42px;height:42px;background:#38bdf8;color:#000000;font-weight:900;border:3px solid #000000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:15px;">{n:02d}</div>'
            elif n in sorteio_set: celulas += f'<div style="width:42px;height:42px;background:#ffffff;color:#000000;font-weight:900;border:3px dashed #000000;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:15px;">{n:02d}</div>'
            else: celulas += f'<div style="width:42px;height:42px;background:#ffffff;color:#000000;border:1px solid #000000;font-weight:900;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:15px;">{n:02d}</div>'
    render_html_seguro(f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box;}}body{{margin:0;padding:0;display:flex;justify-content:center;background:transparent;font-family:Arial,sans-serif;}}.box{{background:#fff;border:4px solid #000000;border-radius:10px;padding:12px;width:fit-content;}}.grid{{display:grid;grid-template-columns:repeat(10,42px);gap:5px;}}</style></head><body><div class="box"><div style="font-weight:900;font-size:16px;margin-bottom:12px;color:#000000;text-align:center;">{titulo}</div><div class="grid">{celulas}</div></div></body></html>''', 390)


# ==============================================================================
# ==============================================================================
# ##############################################################################
# ##############################################################################
# 🛠️ ETAPA 2: INICIALIZAÇÃO DE ESTADO, GERENCIAMENTO E APLICAÇÃO DE PRESETS
# ##############################################################################
# ##############################################################################
# ==============================================================================

if "historico" not in st.session_state:
    st.session_state.historico = [sorted(list(j)) for j in FALLBACK_MEGASENA]
    st.session_state.origem = "Base Local Offline"

if "jogos_aprovados" not in st.session_state: st.session_state.jogos_aprovados = []
if "jogos_upload" not in st.session_state: st.session_state.jogos_upload = []
if "jogos_filtrados_upload" not in st.session_state: st.session_state.jogos_filtrados_upload = []
if "presets_filtros" not in st.session_state: st.session_state.presets_filtros = PRESETS_PADRAO.copy()
if "linha_trabalho_reverso" not in st.session_state: st.session_state.linha_trabalho_reverso = None

dados_calor = calcular_metricas_elliott(st.session_state.historico)
ranking_elliott = sorted(dados_calor.values(), key=lambda x: x["score"], reverse=True)
top_40_dezenas = {item["numero"] for item in ranking_elliott[:40]}
pool_inicial = top_40_dezenas | DEZENAS_BASE_3010
analise_elite = extrair_analise_elite(dados_calor)

if "pool_trabalho" not in st.session_state or not isinstance(st.session_state.pool_trabalho, set):
    st.session_state.pool_trabalho = pool_inicial.copy()

def aplicar_preset(nome_preset):
    cfg_p = st.session_state.presets_filtros.get(nome_preset)
    if not cfg_p: return
    for r in range(6): st.session_state[f"sel_l_{r}"] = cfg_p["linhas"][r]
    for c in range(10): st.session_state[f"sel_c_{c}"] = cfg_p["colunas"][c]
    for d in range(10):
        st.session_state[f"sel_dc_{d}"] = cfg_p["diag_cresc"][d]
        st.session_state[f"sel_dd_{d}"] = cfg_p["diag_decresc"][d]
    st.session_state["sel_primos"] = cfg_p["primos"]
    st.session_state["sel_pares"] = cfg_p["pares"]
    st.session_state["sel_moldura"] = cfg_p["moldura"]
    soma_raw = cfg_p.get("soma", (150, 190))
    st.session_state["sel_soma"] = (int(soma_raw[0]), int(soma_raw[1]))

if "filtro_inicial_carregado" not in st.session_state:
    aplicar_preset("FILTRO3010")
    st.session_state.filtro_inicial_carregado = True

def toggle_dezena(n):
    if not isinstance(st.session_state.pool_trabalho, set):
        st.session_state.pool_trabalho = set(st.session_state.pool_trabalho)
    if n in st.session_state.pool_trabalho: st.session_state.pool_trabalho.remove(n)
    else: st.session_state.pool_trabalho.add(n)


# ==============================================================================
# ==============================================================================
# ##############################################################################
# ##############################################################################
# 🛠️ ETAPA 3: INTERFACE DO APLICATIVO (ABAS 1 A 5)
# ##############################################################################
# ##############################################################################
# ==============================================================================

st.title("🍀 MEGA60 - PAINEL BLINDADO")
st.caption("MATRIZ 6x10 • ALTO CONTRASTE PRETO • MOTOR ROBUSTO SEM RISCO DE FALHA")

tab_cartela, tab_config, tab_volante, tab_upload, tab_historico = st.tabs([
    "🎟️ Cartela & Seleção Elite",
    "🎛️ Filtros & Engenharia Reversa",
    "🗺️ Volante & Raio-X",
    "📥 Upload & Filtragem Sucessiva",
    "📊 Histórico & API Caixa"
])

# ------------------------------------------------------------------------------
# ABA 1: CARTELA & SELEÇÃO ELITE
# ------------------------------------------------------------------------------
with tab_cartela:
    with st.container(border=True):
        st.markdown("### 🏆 NÚMEROS DE ELITE SEPARADOS (FONTE GRANDE E PRETO)")
        c_el1, c_el2, c_el3, c_el4 = st.columns([1, 1, 1, 1.4])
        with c_el1:
            st.markdown("#### 💎 MELHORES PRIMOS")
            st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>{' • '.join([f'{n:02d}' for n in analise_elite['primos']])}</div>", unsafe_allow_html=True)
        with c_el2:
            st.markdown("#### ⚖️ 3 MELHORES PARES")
            st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>{' • '.join([f'{n:02d}' for n in analise_elite['pares']])}</div>", unsafe_allow_html=True)
        with c_el3:
            st.markdown("#### ⚡ MELHORES ÍMPARES")
            st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>{' • '.join([f'{n:02d}' for n in analise_elite['impares']])}</div>", unsafe_allow_html=True)
        with c_el4:
            st.markdown("#### 📐 MELHORES DIAGONAIS")
            dc_badges = "".join([f"<span style='display:inline-block;background:#fef08a;color:#000000;font-weight:900;padding:2px 7px;margin:2px 3px;border:2px solid #000000;border-radius:4px;font-size:1.05rem;'>DC{d+1:02d}</span>" for d in analise_elite["dc"]])
            dd_badges = "".join([f"<span style='display:inline-block;background:#fef08a;color:#000000;font-weight:900;padding:2px 7px;margin:2px 3px;border:2px solid #000000;border-radius:4px;font-size:1.05rem;'>DD{d+1:02d}</span>" for d in analise_elite["dd"]])
            st.markdown(f"<div style='margin-bottom:6px;'><b>CRESCENTES:</b><br>{dc_badges}</div><div><b>DECRESCENTES:</b><br>{dd_badges}</div>", unsafe_allow_html=True)

        st.divider()
        pool_elite_ordenado = analise_elite["pool_elite"]
        st.markdown(f"<div style='font-size:1.35rem;color:#000000;font-weight:900;'>🎯 POOL CONSOLIDADO DAS ELITES ({len(pool_elite_ordenado)} DEZENAS):<br><span style='background:#facc15;padding:6px 14px;border:3px solid #000000;border-radius:6px;display:inline-block;margin-top:8px;'>{' - '.join([f'{n:02d}' for n in pool_elite_ordenado])}</span></div>", unsafe_allow_html=True)

        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button("⭐ CARREGAR SOMENTE ESTE POOL DE ELITE NA CARTELA", use_container_width=True, type="primary"):
                st.session_state.pool_trabalho = set(pool_elite_ordenado)
                st.rerun()
        with c_act2:
            if st.button("🎛️ GERAR E ATIVAR FILTRO COM ESTAS CONDICIONANTES", use_container_width=True):
                preset_elite = extrair_filtros_de_jogo(pool_elite_ordenado, modo="flexivel")
                st.session_state.presets_filtros["FILTRO_ELITE_CONDICIONANTES"] = preset_elite
                aplicar_preset("FILTRO_ELITE_CONDICIONANTES")
                st.success("Filtro ativado na Aba 2!")
                st.rerun()

    st.subheader("🎟️ CARTELA DE 60 NÚMEROS (MATRIZ 6x10)")
    c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)
    with c_b1:
        if st.button("⭐ Base 3010 + Top 40", use_container_width=True):
            st.session_state.pool_trabalho = (top_40_dezenas | DEZENAS_BASE_3010).copy()
            st.rerun()
    with c_b2:
        if st.button("🔥 Apenas Quentes (Top 20)", use_container_width=True):
            st.session_state.pool_trabalho = {item["numero"] for item in ranking_elliott[:20]}
            st.rerun()
    with c_b3:
        if st.button("⚡ +9 Fibonacci", use_container_width=True):
            st.session_state.pool_trabalho = set(st.session_state.pool_trabalho) | FIBONACCI_MEGASENA
            st.rerun()
    with c_b4:
        if st.button("✅ Marcar Todas (60)", use_container_width=True):
            st.session_state.pool_trabalho = set(range(1, 61))
            st.rerun()
    with c_b5:
        if st.button("🧹 Limpar Cartela", use_container_width=True):
            st.session_state.pool_trabalho = set()
            st.rerun()

    set_elite = set(analise_elite["pool_elite"])
    for r in range(6):
        cols = st.columns(10)
        for c in range(10):
            n = r * 10 + c + 1
            meta = dados_calor[n]
            esta_ativa = n in st.session_state.pool_trabalho
            with cols[c]:
                if st.button(f"{n:02d}{'⭐' if n in set_elite else ''}\n({meta['score']:.0f}p)", key=f"btn_num_{n}", type="primary" if esta_ativa else "secondary", use_container_width=True):
                    toggle_dezena(n)
                    st.rerun()

    st.divider()
    col_inf1, col_inf2 = st.columns([3, 1])
    qtd_sel = len(st.session_state.pool_trabalho)
    with col_inf1:
        st.markdown(f"<div style='font-size:1.3rem;font-weight:900;background:#fef08a;border:3px solid #000000;padding:12px;border-radius:8px;'>DEZENAS ATIVAS ({qtd_sel}):<br>{' - '.join([f'{n:02d}' for n in sorted(list(st.session_state.pool_trabalho))]) if qtd_sel else 'NENHUMA'}</div>", unsafe_allow_html=True)
    with col_inf2:
        st.metric("Total Selecionado", f"{qtd_sel} / 60")
        st.markdown(f"<div style='font-size:1.2rem;font-weight:900;'>Jogos Brutos: {math.comb(qtd_sel, 6) if qtd_sel >= 6 else 0:,}</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ABA 2: CONFIGURAÇÃO DE FILTROS & ENGENHARIA REVERSA (COM GRAVAÇÃO MANUAL)
# ------------------------------------------------------------------------------
with tab_config:
    st.markdown("### 🎛️ FILTROS ESTRUTURAIS & ENGENHARIA REVERSA")
    tipo_reverso = st.radio("Selecione a Rotina de Engenharia Reversa:", ["🏛️ Rotina 1: Histórica Multiconcursos", "⚡ Rotina 2: Amostra Personalizada"], horizontal=True)

    if tipo_reverso.startswith("🏛️ Rotina 1"):
        with st.container(border=True):
            st.markdown("#### 🏛️ ENGENHARIA REVERSA MULTICONCURSOS")
            total_disp = len(st.session_state.historico)
            col_m1, col_m2, col_m3 = st.columns([1.5, 1.8, 1.7])
            with col_m1: qtd_concursos_sel = st.slider("Concursos Anteriores:", 1, max(1, total_disp), min(10, total_disp))
            with col_m2:
                nome_filtro_multi = st.text_input("Nome do Filtro:", value=f"FILTRO_ULT_{qtd_concursos_sel}_CONCURSOS")
                carregar_pool_multi = st.checkbox("Carregar Dezenas no Pool Ativo", value=True)
            with col_m3: tolerancia_multi = st.selectbox("Margem:", ["Envelope Preciso", "Envelope Flexível"], index=0)

            if st.button("🚀 PROCESSAR CONCURSOS E ATIVAR FILTRO", type="primary", use_container_width=True):
                sorteios_alvo = st.session_state.historico[-qtd_concursos_sel:]
                preset_multi = extrair_filtros_multiconcursos(sorteios_alvo, modo="preciso" if "Preciso" in tolerancia_multi else "flexivel")
                nome_salvar = nome_filtro_multi.strip() or f"FILTRO_ULT_{qtd_concursos_sel}_CONCURSOS"
                st.session_state.presets_filtros[nome_salvar] = preset_multi
                aplicar_preset(nome_salvar)
                dezenas_unicas = sorted(list({n for j in sorteios_alvo for n in j}))
                if carregar_pool_multi: st.session_state.pool_trabalho = set(dezenas_unicas)
                st.success(f"Filtro '{nome_salvar}' ativado!")
                st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### ⚡ ENGENHARIA REVERSA POR DEZENAS DIGITADAS")
            if "input_dezenas_digitadas_texto" not in st.session_state: st.session_state.input_dezenas_digitadas_texto = "10 17 42 43 57 59"
            col_input_res, col_input_nome, col_input_tipo = st.columns([2.5, 1.8, 1.7])
            with col_input_res: entrada_dezenas_filtro = st.text_area("Dezenas (6 a 60 números):", value=st.session_state.input_dezenas_digitadas_texto, height=75)
            with col_input_nome:
                nome_filtro_novo = st.text_input("Nome do Filtro:", value="MEU_NOVO_FILTRO")
                substituir_pool_opcao = st.checkbox("Limpar Pool Anterior", value=True)
            with col_input_tipo: tipo_tolerancia = st.selectbox("Nível de Tolerância:", ["Perfil Flexível", "Perfil Exato"], index=0)

            if st.button("⚡ GERAR, GRAVAR E ATIVAR FILTRO", type="primary", use_container_width=True):
                nums_parse = [int(x) for x in re.findall(r"\b\d+\b", entrada_dezenas_filtro)]
                dezenas_limpas = sorted(list(set([n for n in nums_parse if 1 <= n <= 60])))
                if len(dezenas_limpas) < 6: st.error("Informe pelo menos 6 dezenas válidas.")
                else:
                    st.session_state.input_dezenas_digitadas_texto = " ".join([f"{n:02d}" for n in dezenas_limpas])
                    preset_extraido = extrair_filtros_de_jogo(dezenas_limpas, modo="exato" if "Exato" in tipo_tolerancia else "flexivel")
                    nome_salvar = nome_filtro_novo.strip() or "MEU_NOVO_FILTRO"
                    st.session_state.presets_filtros[nome_salvar] = preset_extraido
                    aplicar_preset(nome_salvar)
                    if substituir_pool_opcao: st.session_state.pool_trabalho = set(dezenas_limpas)
                    st.success(f"Filtro '{nome_salvar}' ativado!")
                    st.rerun()

    # GERENCIADOR DE PREDEFINIÇÕES & GRAVAÇÃO MANUAL
    with st.container(border=True):
        st.markdown("#### 💾 GERENCIADOR DE PREDEFINIÇÕES & GRAVAÇÃO MANUAL")
        col_puxar, col_gravar = st.columns(2)
        with col_puxar:
            lista_nomes = list(st.session_state.presets_filtros.keys())
            filtro_escolhido = st.selectbox("Carregar Filtro Salvo:", lista_nomes, key="select_preset_load")
            c_pux1, c_pux2 = st.columns(2)
            with c_pux1:
                if st.button("🚀 APLICAR PREDEFINIÇÃO", use_container_width=True):
                    aplicar_preset(filtro_escolhido)
                    st.success(f"Filtro '{filtro_escolhido}' carregado com sucesso!")
                    st.rerun()
            with c_pux2:
                st.download_button("💾 BAIXAR (.JSON)", data=json.dumps(st.session_state.presets_filtros, indent=2, ensure_ascii=False), file_name="meus_filtros_mega60.json", mime="application/json", use_container_width=True)

        with col_gravar:
            nome_novo_filtro = st.text_input("Nome da Nova Configuração:", placeholder="Ex: Meu Filtro Top", key="input_nome_filtro_manual")
            if st.button("💾 GRAVAR CONFIGURAÇÃO MANUAL", use_container_width=True, type="primary"):
                if not nome_novo_filtro.strip(): st.error("Informe um nome para a predefinição.")
                else:
                    novo_preset = {
                        "linhas": [st.session_state.get(f"sel_l_{r}", "0 a 2") for r in range(6)],
                        "colunas": [st.session_state.get(f"sel_c_{c}", "0 a 2") for c in range(10)],
                        "diag_cresc": [st.session_state.get(f"sel_dc_{d}", "0 a 2") for d in range(10)],
                        "diag_decresc": [st.session_state.get(f"sel_dd_{d}", "0 a 2") for d in range(10)],
                        "primos": st.session_state.get("sel_primos", [3]),
                        "pares": st.session_state.get("sel_pares", ["2P / 4I"]),
                        "moldura": st.session_state.get("sel_moldura", [5]),
                        "soma": (int(st.session_state.get("sel_soma", (150, 190))[0]), int(st.session_state.get("sel_soma", (150, 190))[1]))
                    }
                    st.session_state.presets_filtros[nome_novo_filtro.strip()] = novo_preset
                    st.success(f"Predefinição '{nome_novo_filtro.strip()}' gravada com sucesso!")
                    st.rerun()

    st.divider()
    opcoes_nomes = list(OPCOES_QUANTIDADE.keys())

    with st.container(border=True):
        st.markdown("#### 1️⃣ LINHAS INDIVIDUAIS (L01 a L06)")
        cols_l = st.columns(6)
        limites_linhas = []
        for r in range(6):
            with cols_l[r]:
                esc = st.selectbox(f"Linha {r+1:02d}", opcoes_nomes, key=f"sel_l_{r}")
                limites_linhas.append(OPCOES_QUANTIDADE[esc])

    with st.container(border=True):
        st.markdown("#### 2️⃣ COLUNAS INDIVIDUAIS (C01 a C10)")
        cols_c_up, cols_c_dw = st.columns(5), st.columns(5)
        limites_colunas = []
        for c in range(10):
            alvo = cols_c_up[c] if c < 5 else cols_c_dw[c - 5]
            with alvo:
                esc = st.selectbox(f"Coluna {c+1:02d}", opcoes_nomes, key=f"sel_c_{c}")
                limites_colunas.append(OPCOES_QUANTIDADE[esc])

    c_diag1, c_diag2 = st.columns(2)
    with c_diag1:
        with st.container(border=True):
            st.markdown("#### 3️⃣ DIAGONAIS CRESCENTES (DC01 a DC10 /)")
            with st.expander("Expandir Diagonais Crescentes", expanded=False):
                limites_dc = []
                for d in range(10):
                    esc = st.selectbox(f"DC{d+1:02d}", opcoes_nomes, key=f"sel_dc_{d}")
                    limites_dc.append(OPCOES_QUANTIDADE[esc])
    with c_diag2:
        with st.container(border=True):
            st.markdown("#### 4️⃣ DIAGONAIS DECRESCENTES (DD01 a DD10 \\)")
            with st.expander("Expandir Diagonais Decrescentes", expanded=False):
                limites_dd = []
                for d in range(10):
                    esc = st.selectbox(f"DD{d+1:02d}", opcoes_nomes, key=f"sel_dd_{d}")
                    limites_dd.append(OPCOES_QUANTIDADE[esc])

    with st.container(border=True):
        st.markdown("#### 5️⃣ PRIMOS, PARES, MOLDURA E FAIXA DE SOMA")
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        with c_p1: primos_sel = st.multiselect("Primos:", list(range(7)), default=st.session_state.get("sel_primos", [3]), key="sel_primos")
        with c_p2:
            opcoes_par = {"3P / 3I": 3, "2P / 4I": 2, "4P / 2I": 4, "1P / 5I": 1, "5P / 1I": 5, "0P / 6I": 0, "6P / 0I": 6}
            par_sel = st.multiselect("Pares/Ímpares:", list(opcoes_par.keys()), default=st.session_state.get("sel_pares", ["2P / 4I"]), key="sel_pares")
            pares_valores = {opcoes_par[k] for k in par_sel}
        with c_p3: moldura_sel = st.multiselect("Moldura:", list(range(7)), default=st.session_state.get("sel_moldura", [5]), key="sel_moldura")
        with c_p4:
            val_soma_estado = st.session_state.get("sel_soma", (150, 190))
            soma_min_val, soma_max_val = (int(val_soma_estado[0]), int(val_soma_estado[1])) if isinstance(val_soma_estado, (list, tuple)) and len(val_soma_estado) == 2 else (150, 190)
            faixa_soma = st.slider("Faixa de Soma:", 50, 320, (soma_min_val, soma_max_val), key="sel_soma")

    config_total = {
        "linhas": limites_linhas, "colunas": limites_colunas, "diag_cresc": limites_dc,
        "diag_decresc": limites_dd, "primos_aceitos": set(primos_sel), "pares_aceitos": pares_valores,
        "moldura_aceita": set(moldura_sel), "faixa_soma": faixa_soma
    }

    st.divider()
    if st.button("🚀 GERAR E FILTRAR APOSTAS", use_container_width=True, type="primary"):
        with st.spinner("🛠️ Processando Motor Combinatório..."):
            resultados = executar_varredura_pool(st.session_state.pool_trabalho, config_total, st.empty(), st.empty(), teto_max=None)
            st.session_state.jogos_aprovados = resultados
            if resultados: st.success(f"✅ Sucesso: {len(resultados):,} apostas geradas.")
            else: st.warning("⚠️ Nenhuma combinação atendeu aos filtros.")

    if st.session_state.jogos_aprovados:
        st.success(f"Total Aprovado: {len(st.session_state.jogos_aprovados):,} apostas.")
        st.download_button("📥 BAIXAR JOGOS APROVADOS (.TXT)", data="\n".join([" ".join([f"{n:02d}" for n in sorted(j)]) for j in st.session_state.jogos_aprovados]), file_name="mega60_apostas_filtradas.txt", mime="text/plain", use_container_width=True)

# ------------------------------------------------------------------------------
# ABA 3: VOLANTE VISUAL & RAIO-X
# ------------------------------------------------------------------------------
with tab_volante:
    st.subheader("DISSECAÇÃO DA CARTELA")
    jogos_exibir = st.session_state.jogos_aprovados or st.session_state.jogos_upload

    if jogos_exibir:
        total_jogos = len(jogos_exibir)
        st.markdown(f"**Total de jogos disponíveis para inspeção:** `{total_jogos:,}`")
        
        if total_jogos > 1:
            sel_idx = st.slider("Escolha o número da aposta para inspecionar:", 1, total_jogos, 1)
        else:
            sel_idx = 1

        jogo_ativo = sorted(jogos_exibir[sel_idx - 1])
        render_volante_conferencia(jogo_ativo, [], f"JOGO #{sel_idx:04d}: {' - '.join([f'{n:02d}' for n in jogo_ativo])}")
    else:
        st.info("Gere apostas na Aba 2 ou carregue um arquivo na Aba 4 para inspecionar no volante.")
# ------------------------------------------------------------------------------
# ABA 4: UPLOAD & FILTRAGEM SUCESSIVA & CONFERÊNCIA
# ------------------------------------------------------------------------------
with tab_upload:
    st.subheader("📥 UPLOAD, FILTRAGEM & CONFERÊNCIA")
    arquivo_enviado = st.file_uploader("Carregue seu arquivo de apostas (.txt ou .csv):", type=["txt", "csv"])

    if arquivo_enviado is not None:
        conteudo = arquivo_enviado.read()
        jogos_carregados, invalidos = processar_arquivo_upload(conteudo)
        st.session_state.jogos_upload = jogos_carregados
        if invalidos > 0:
            st.warning(f"⚠️ {invalidos} linha(s) ignoradas.")

    if st.session_state.jogos_upload:
        jogos_up = st.session_state.jogos_upload
        total_up = len(jogos_up)
        st.success(f"Arquivo Carregado: {total_up:,} apostas em memória.")

        with st.container(border=True):
            st.markdown("#### ⚡ FILTRAR ARQUIVO CARREGADO")
            c_flt1, c_flt2 = st.columns([2, 1])
            with c_flt1:
                if st.button("🔍 APLICAR FILTROS ATIVOS NO ARQUIVO", type="primary", use_container_width=True):
                    with st.spinner("Filtrando apostas..."):
                        aprovados_do_arquivo = [j for j in jogos_up if validar_aposta_final_6(tuple(j), config_total)]
                        st.session_state.jogos_filtrados_upload = aprovados_do_arquivo
                        st.success(f"{len(aprovados_do_arquivo):,} de {total_up:,} aprovadas.")

            if st.session_state.jogos_filtrados_upload:
                qtd_flt = len(st.session_state.jogos_filtrados_upload)
                txt_flt = "\n".join([" ".join([f"{n:02d}" for n in sorted(j)]) for j in st.session_state.jogos_filtrados_upload])
                with c_flt2:
                    st.download_button(f"💾 BAIXAR LOTE FILTRADO ({qtd_flt:,})", data=txt_flt, file_name=f"mega60_lote_filtrado.txt", mime="text/plain", use_container_width=True)

        st.divider()
        col_diag_left, col_conf_right = st.columns([1, 1], gap="large")

        with col_diag_left:
            st.markdown("### 📊 DIAGNÓSTICO DO ARQUIVO")
            cnt_nums = Counter()
            somas = []
            for j in jogos_up:
                cnt_nums.update(j)
                somas.append(sum(j))

            m1, m2, m3 = st.columns(3)
            m1.metric("Total", f"{total_up:,}")
            m2.metric("Soma Média", f"{sum(somas)/len(somas):.1f}")
            m3.metric("Mais Frequente", f"{cnt_nums.most_common(1)[0][0]:02d}")

            st.markdown("#### 🔥 FREQUÊNCIA NA MATRIZ")
            celulas_up_heat = ""
            for r in range(6):
                for c in range(10):
                    n = r * 10 + c + 1
                    freq = cnt_nums[n]
                    bg = "#ffffff" if freq == 0 else "#fef08a"
                    celulas_up_heat += f'<div style="width:40px;height:40px;background:{bg};color:#000000;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:monospace;border:2px solid #000000;box-sizing:border-box;"><span style="font-size:13px;font-weight:900;">{n:02d}</span><span style="font-size:10px;font-weight:900;">{freq}x</span></div>'

            render_html_seguro(f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box;}}body{{margin:0;padding:0;background:transparent;display:flex;justify-content:center;font-family:Arial,sans-serif;}}.box{{background:#fff;border:4px solid #000000;border-radius:10px;padding:10px;width:fit-content;}}.grid{{display:grid;grid-template-columns:repeat(10,40px);gap:4px;}}</style></head><body><div class="box"><div class="grid">{celulas_up_heat}</div></div></body></html>', 310)

        with col_conf_right:
            st.markdown("### 🎯 CONFERÊNCIA DE RESULTADOS")
            ult_sorteio = st.session_state.historico[-1] if st.session_state.historico else [4, 12, 18, 30, 35, 54]
            
            # AQUI ESTÁ O SELECTOR DE MODO (Oficial vs Manual)
            modo_origem = st.radio("Origem:", ["Último Sorteio Oficial", "Digitar Manualmente"], horizontal=True)
            
            if modo_origem == "Último Sorteio Oficial":
                dezenas_conf = sorted(ult_sorteio)
            else:
                # 👉 É NESTA LINHA QUE APARECE A CAIXA PARA DIGITAR AS 6 DEZENAS MANUAIS:
                entrada_manual = st.text_input("6 Dezenas Sorteadas:", value=" ".join([f"{n:02d}" for n in sorted(ult_sorteio)]))
                nums_man = [int(x) for x in re.findall(r"\b\d+\b", entrada_manual)]
                dezenas_conf = sorted(list(set([n for n in nums_man if 1 <= n <= 60])))

            if len(dezenas_conf) != 6:
                st.error("Informe exatamente 6 dezenas distintas entre 01 e 60.")
            else:
                render_cartao_sorteio_html(dezenas_conf, titulo="SORTEIO CONFERIDO")
                base_conferir = st.session_state.jogos_filtrados_upload or jogos_up
                relatorio_conf, placar_conf = conferir_apostas_contra_sorteio(base_conferir, dezenas_conf)

                c_s, c_q, c_qd, c_t = st.columns(4)
                c_s.metric("Sena (6)", f"{len(placar_conf[6])}")
                c_q.metric("Quina (5)", f"{len(placar_conf[5])}")
                c_qd.metric("Quadra (4)", f"{len(placar_conf[4])}")
                c_t.metric("Terno (3)", f"{len(placar_conf[3])}")

                tot_prem = len(placar_conf[6]) + len(placar_conf[5]) + len(placar_conf[4])
                if tot_prem > 0:
                    st.success(f"🎉 {tot_prem} aposta(s) premiada(s) encontradas!")
                    jogos_premiados_txt = "\n".join([f"{' '.join([f'{n:02d}' for n in it['jogo']])} | {it['qtd_acertos']} ACERTOS" for it in relatorio_conf if it["qtd_acertos"] >= 4])
                    st.download_button("📥 BAIXAR APOSTAS PREMIADAS (.TXT)", data=jogos_premiados_txt, file_name="mega60_premiadas.txt", mime="text/plain", use_container_width=True)
                else:
                    st.warning("Nenhuma aposta alcançou 4, 5 ou 6 acertos.")
                 jogos_com_acerto = [it for it in relatorio_conf if it["qtd_acertos"] >= 4] or relatorio_conf
                opcoes_map = {it["num_aposta"]: f"Aposta #{it['num_aposta']:04d} — {it['qtd_acertos']} acertos" for it in jogos_com_acerto[:50]}
                if opcoes_map:
                    idx_escolhido = st.selectbox("Inspecionar no Volante:", list(opcoes_map.keys()), format_func=lambda x: opcoes_map[x])
                    if idx_escolhido is not None:
                        item_ativo = next(it for it in relatorio_conf if it["num_aposta"] == idx_escolhido)
                        render_volante_conferencia(item_ativo["jogo"], dezenas_conf, titulo=f"Aposta #{item_ativo['num_aposta']:04d} ({item_ativo['qtd_acertos']} Acertos)")
    else:
        st.info("Carregue um arquivo .txt ou .csv na parte superior para ativar o painel de conferência.")

# ------------------------------------------------------------------------------
# ABA 5: HISTÓRICO & API CAIXA
# ------------------------------------------------------------------------------
with tab_historico:
    st.subheader("BASE DE CONCURSOS OFICIAIS")
    if st.button("🌐 SINCRONIZAR COM A CAIXA AGORA", type="primary"):
        r = requests.get("https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena", timeout=10, verify=False)
        if r.status_code == 200:
            ult = r.json()
            dezenas_sorteadas = sorted([int(x) for x in ult.get("listaDezenas", [])])
            if len(dezenas_sorteadas) == 6 and dezenas_sorteadas not in st.session_state.historico:
                st.session_state.historico.append(dezenas_sorteadas)
                st.success(f"Concurso #{ult.get('numero')} sincronizado!")
                st.rerun()
