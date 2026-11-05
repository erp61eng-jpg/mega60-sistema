import streamlit as st
from itertools import combinations

st.set_page_config(page_title="MEGA60 - Sistema", layout="wide")

# Alto contraste total: preto puro, negrito absoluto, botões ativos em amarelo ouro
st.markdown("""
<style>
    html, body, [class*="css"], .stMarkdown, p, span, label, div, input, textarea, select {
        color: #000000 !important;
        font-weight: 800 !important;
        font-family: Arial, Helvetica, sans-serif !important;
    }
    h1, h2, h3, h4 {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    .stButton > button {
        color: #000000 !important;
        font-size: 1.15rem !important;
        font-weight: 900 !important;
        border: 2px solid #000000 !important;
        background-color: #ffffff !important;
        height: 3.2rem !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #facc15 !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Definições analíticas
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}
MOLDURA = set(range(1, 11)) | set(range(51, 61)) | {r * 10 + 1 for r in range(6)} | {r * 10 + 10 for r in range(6)}

ELITE_PRIMOS = [5, 11, 13, 29, 41]
ELITE_PARES = [16, 40, 58]
ELITE_IMPARES = [9, 35, 47, 53, 59]
POOL_ELITE = sorted(list(set(ELITE_PRIMOS + ELITE_PARES + ELITE_IMPARES)))

if "selecionadas" not in st.session_state:
    st.session_state.selecionadas = set(range(1, 61))

if "apostas" not in st.session_state:
    st.session_state.apostas = []

st.title("🍀 MEGA60 - SISTEMA OPERACIONAL")

# --- GRUPO DE ELITE ---
st.subheader("🏆 NÚMEROS DE ELITE")
c1, c2, c3 = st.columns(3)
c1.markdown(f"**💎 PRIMOS:**<br>{' • '.join([f'{n:02d}' for n in ELITE_PRIMOS])}", unsafe_allow_html=True)
c2.markdown(f"**⚖️ 3 MELHORES PARES:**<br>{' • '.join([f'{n:02d}' for n in ELITE_PARES])}", unsafe_allow_html=True)
c3.markdown(f"**⚡ MELHORES ÍMPARES:**<br>{' • '.join([f'{n:02d}' for n in ELITE_IMPARES])}", unsafe_allow_html=True)

st.markdown(f"**Pool Consolidado ({len(POOL_ELITE)} dezenas):** `{' - '.join([f'{n:02d}' for n in POOL_ELITE])}`")
if st.button("⭐ Carregar Somente Pool de Elite na Cartela", type="primary"):
    st.session_state.selecionadas = set(POOL_ELITE)
    st.rerun()

st.divider()

# --- MATRIZ 6x10 ---
st.subheader("🎟️ CARTELA 6x10 (MATRIZ INTERATIVA)")
col_a, col_b = st.columns(2)
with col_a:
    if st.button("✅ Marcar Todas (60)"):
        st.session_state.selecionadas = set(range(1, 61))
        st.rerun()
with col_b:
    if st.button("🧹 Limpar Cartela"):
        st.session_state.selecionadas = set()
        st.rerun()

for r in range(6):
    cols = st.columns(10)
    for c in range(10):
        n = r * 10 + c + 1
        ativo = n in st.session_state.selecionadas
        tipo = "primary" if ativo else "secondary"
        with cols[c]:
            if st.button(f"{n:02d}", key=f"btn_{n}", type=tipo):
                if ativo:
                    st.session_state.selecionadas.remove(n)
                else:
                    st.session_state.selecionadas.add(n)
                st.rerun()

st.markdown(f"### Total Selecionado: **{len(st.session_state.selecionadas)} / 60**")

st.divider()

# --- FILTROS E PROCESSAMENTO ---
st.subheader("⚙️ FILTROS")
f1, f2, f3 = st.columns(3)
with f1:
    soma_min, soma_max = st.slider("Faixa de Soma:", 50, 320, (140, 210))
with f2:
    pares_permitidos = st.multiselect("Quantidade de Pares:", [0, 1, 2, 3, 4, 5, 6], default=[2, 3, 4])
with f3:
    limite = st.number_input("Teto Máximo de Jogos:", min_value=10, max_value=50000, value=1000, step=500)

if st.button("🚀 GERAR JOGOS FILTRADOS", type="primary"):
    dezenas = sorted(list(st.session_state.selecionadas))
    if len(dezenas) < 6:
        st.error("Selecione pelo menos 6 dezenas na cartela.")
    else:
        aprovados = []
        for comb in combinations(dezenas, 6):
            s = sum(comb)
            if not (soma_min <= s <= soma_max):
                continue
            
            p = sum(1 for x in comb if x % 2 == 0)
            if pares_permitidos and p not in pares_permitidos:
                continue

            aprovados.append(sorted(comb))
            if len(aprovados) >= limite:
                break

        st.session_state.apostas = aprovados
        st.success(f"{len(aprovados)} jogos gerados e aprovados com sucesso!")

if st.session_state.apostas:
    linhas = [" ".join([f"{n:02d}" for n in j]) for j in st.session_state.apostas]
    st.text_area("Apostas Geradas (Ordenadas do menor para o maior):", value="\n".join(linhas), height=220)
    st.download_button(
        "💾 Baixar Apostas (.txt)",
        data="\n".join(linhas),
        file_name="jogos_megasena.txt",
        mime="text/plain"
    )
