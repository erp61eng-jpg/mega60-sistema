# ==============================================================================
# INICIALIZAÇÃO DE ESTADO
# ==============================================================================
if "historico" not in st.session_state:
    st.session_state.historico = [sorted(list(j)) for j in FALLBACK_MEGASENA]
    st.session_state.origem = "Base Local Offline"

if "jogos_aprovados" not in st.session_state:
    st.session_state.jogos_aprovados = []

if "jogos_upload" not in st.session_state:
    st.session_state.jogos_upload = []

if "jogos_filtrados_upload" not in st.session_state:
    st.session_state.jogos_filtrados_upload = []

if "presets_filtros" not in st.session_state:
    st.session_state.presets_filtros = PRESETS_PADRAO.copy()

if "input_resultado_reverso_val" not in st.session_state:
    ult_res = st.session_state.historico[-1] if st.session_state.historico else [5, 9, 16, 40, 41, 59]
    st.session_state.input_resultado_reverso_val = " ".join([f"{n:02d}" for n in sorted(ult_res)])

if "linha_trabalho_reverso" not in st.session_state:
    st.session_state.linha_trabalho_reverso = None

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
    for r in range(6):
        st.session_state[f"sel_l_{r}"] = cfg_p["linhas"][r]
    for c in range(10):
        st.session_state[f"sel_c_{c}"] = cfg_p["colunas"][c]
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
    if n in st.session_state.pool_trabalho:
        st.session_state.pool_trabalho.remove(n)
    else:
        st.session_state.pool_trabalho.add(n)

def cb_puxar_ultimo():
    if st.session_state.historico:
        st.session_state.input_resultado_reverso_val = " ".join(
            [f"{n:02d}" for n in sorted(st.session_state.historico[-1])]
        )

# ==============================================================================
# INTERFACE PRINCIPAL
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

# ==============================================================================
# ABA 1: CARTELA & PAINEL DE ELITE
# ==============================================================================
with tab_cartela:
    with st.container(border=True):
        st.markdown("### 🏆 NÚMEROS DE ELITE SEPARADOS (FONTE GRANDE E PRETO)")
        st.markdown("**Calculados pelo Motor de Elliott sobre os concursos ativos:**")

        c_el1, c_el2, c_el3, c_el4 = st.columns([1, 1, 1, 1.4])

        with c_el1:
            st.markdown("#### 💎 MELHORES PRIMOS")
            p_txt = " • ".join([f"{n:02d}" for n in analise_elite["primos"]])
            st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>{p_txt}</div>", unsafe_allow_html=True)

        with c_el2:
            st.markdown("#### ⚖️ 3 MELHORES PARES")
            pa_txt = " • ".join([f"{n:02d}" for n in analise_elite["pares"]])
            st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>{pa_txt}</div>", unsafe_allow_html=True)

        with c_el3:
            st.markdown("#### ⚡ MELHORES ÍMPARES")
            i_txt = " • ".join([f"{n:02d}" for n in analise_elite["impares"]])
            st.markdown(f"<div style='font-size:1.5rem;color:#000000;font-weight:900;'>{i_txt}</div>", unsafe_allow_html=True)

        with c_el4:
            st.markdown("#### 📐 MELHORES DIAGONAIS")
            dc_badges = "".join([f"<span style='display:inline-block;background:#fef08a;color:#000000;font-weight:900;padding:2px 7px;margin:2px 3px;border:2px solid #000000;border-radius:4px;font-size:1.05rem;'>DC{d+1:02d}</span>" for d in analise_elite["dc"]])
            dd_badges = "".join([f"<span style='display:inline-block;background:#fef08a;color:#000000;font-weight:900;padding:2px 7px;margin:2px 3px;border:2px solid #000000;border-radius:4px;font-size:1.05rem;'>DD{d+1:02d}</span>" for d in analise_elite["dd"]])
            st.markdown(f"""
            <div style='margin-bottom:6px;line-height:1.5;'>
                <span style='font-size:1.05rem;font-weight:900;color:#000000;'>CRESCENTES (↗):</span><br>{dc_badges}
            </div>
            <div style='line-height:1.5;'>
                <span style='font-size:1.05rem;font-weight:900;color:#000000;'>DECRESCENTES (↘):</span><br>{dd_badges}
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        pool_elite_ordenado = analise_elite["pool_elite"]
        dezenas_elite_txt = " - ".join([f"{n:02d}" for n in pool_elite_ordenado])
        st.markdown(
            f"<div style='font-size:1.35rem;color:#000000;font-weight:900;padding:8px 0;'>"
            f"🎯 POOL CONSOLIDADO DAS ELITES ({len(pool_elite_ordenado)} DEZENAS AGRUPADAS):<br>"
            f"<span style='background:#facc15;padding:6px 14px;border:3px solid #000000;border-radius:6px;display:inline-block;margin-top:8px;'>"
            f"{dezenas_elite_txt}</span></div>",
            unsafe_allow_html=True
        )

        c_act1, c_act2 = st.columns([1, 1])
        with c_act1:
            if st.button("⭐ CARREGAR SOMENTE ESTE POOL DE ELITE NA CARTELA", use_container_width=True, type="primary"):
                st.session_state.pool_trabalho = set(pool_elite_ordenado)
                st.rerun()

        with c_act2:
            if st.button("🎛️ GERAR E ATIVAR FILTRO COM ESTAS CONDICIONANTES", use_container_width=True):
                preset_elite = extrair_filtros_de_jogo(pool_elite_ordenado, modo="flexivel")
                st.session_state.presets_filtros["FILTRO_ELITE_CONDICIONANTES"] = preset_elite
                aplicar_preset("FILTRO_ELITE_CONDICIONANTES")
                st.success("FILTRO 'FILTRO_ELITE_CONDICIONANTES' ATIVADO NA ABA 2!")
                st.rerun()

    st.write("")

    st.subheader("🎟️ CARTELA DE 60 NÚMEROS (MATRIZ 6x10)")
    st.markdown("**AMARELO = MARCADO NO POOL | BRANCO = NÃO MARCADO | ⭐ = ELITE**")

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

    st.write("")

    set_elite = set(analise_elite["pool_elite"])

    for r in range(6):
        cols = st.columns(10)
        for c in range(10):
            n = r * 10 + c + 1
            meta = dados_calor[n]
            esta_ativa = n in st.session_state.pool_trabalho
            e_elite = n in set_elite

            tipo_btn = "primary" if esta_ativa else "secondary"
            star_ico = "⭐" if e_elite else ""
            rotulo = f"{n:02d}{star_ico}\n({meta['score']:.0f}p)"

            with cols[c]:
                if st.button(rotulo, key=f"btn_num_{n}", type=tipo_btn, use_container_width=True):
                    toggle_dezena(n)
                    st.rerun()

    st.divider()
    col_inf1, col_inf2 = st.columns([3, 1])
    qtd_sel = len(st.session_state.pool_trabalho)
    with col_inf1:
        dezenas_txt = " - ".join([f"{n:02d}" for n in sorted(list(st.session_state.pool_trabalho))])
        st.markdown(
            f"<div style='font-size:1.3rem;font-weight:900;color:#000000;background:#fef08a;border:3px solid #000000;padding:12px;border-radius:8px;'>"
            f"DEZENAS ATIVAS NO POOL ({qtd_sel}):<br>{dezenas_txt if dezenas_txt else 'NENHUMA SELECIONADA'}</div>",
            unsafe_allow_html=True
        )
    with col_inf2:
        total_comb = math.comb(qtd_sel, 6) if qtd_sel >= 6 else 0
        st.metric("Total Selecionado", f"{qtd_sel} / 60")
        st.markdown(f"<div style='font-size:1.2rem;font-weight:900;color:#000000;'>Jogos Brutos: {total_comb:,}</div>", unsafe_allow_html=True)

# ==============================================================================
# ABA 2: CONFIGURAÇÃO DOS FILTROS & MOTOR COMBINATÓRIO
# ==============================================================================
with tab_config:
    st.markdown("### 🎛️ FILTROS ESTRUTURAIS & ENGENHARIA REVERSA")

    tipo_reverso = st.radio(
        "Selecione a Rotina de Engenharia Reversa:",
        [
            "🏛️ Rotina 1: Histórica Multiconcursos (Concursos Anteriores em Lote)",
            "⚡ Rotina 2: Amostra Personalizada (Digitar 6 a 60 Dezenas)"
        ],
        horizontal=True
    )

    if tipo_reverso.startswith("🏛️ Rotina 1"):
        with st.container(border=True):
            st.markdown("#### 🏛️ ENGENHARIA REVERSA MULTICONCURSOS")
            total_disp = len(st.session_state.historico)
            col_m1, col_m2, col_m3 = st.columns([1.5, 1.8, 1.7])
            with col_m1:
                qtd_concursos_sel = st.slider(
                    "Concursos Anteriores:",
                    min_value=1,
                    max_value=max(1, total_disp),
                    value=min(10, total_disp)
                )
            with col_m2:
                nome_filtro_multi = st.text_input(
                    "Nome do Filtro:",
                    value=f"FILTRO_ULT_{qtd_concursos_sel}_CONCURSOS",
                    key="input_nome_multi"
                )
                carregar_pool_multi = st.checkbox(
                    "Carregar Dezenas no Pool Ativo",
                    value=True
                )
            with col_m3:
                tolerancia_multi = st.selectbox(
                    "Margem Estrutural:",
                    ["Envelope Preciso (100% dos Sorteios)", "Envelope Flexível (Margem +1 / -1)"],
                    index=0,
                    key="sel_tolerancia_multi"
                )

            if st.button("🚀 PROCESSAR CONCURSOS, CRIAR E ATIVAR FILTRO", type="primary", use_container_width=True):
                with st.spinner("Processando..."):
                    sorteios_alvo = st.session_state.historico[-qtd_concursos_sel:]
                    modo_extrair = "preciso" if tolerancia_multi.startswith("Envelope Preciso") else "flexivel"
                    preset_multi = extrair_filtros_multiconcursos(sorteios_alvo, modo=modo_extrair)
                    
                    nome_salvar = nome_filtro_multi.strip() or f"FILTRO_ULT_{qtd_concursos_sel}_CONCURSOS"
                    audit_dados = preset_multi.pop("audit")
                    
                    st.session_state.presets_filtros[nome_salvar] = preset_multi
                    aplicar_preset(nome_salvar)

                    dezenas_unicas_periodo = sorted(list({n for j in sorteios_alvo for n in j}))

                    if carregar_pool_multi:
                        st.session_state.pool_trabalho = set(dezenas_unicas_periodo)
                    else:
                        st.session_state.pool_trabalho = set(st.session_state.pool_trabalho) | set(dezenas_unicas_periodo)

                    hora_agora = time.strftime("%H:%M:%S - %d/%m/%Y")
                    st.session_state.linha_trabalho_reverso = {
                        "tipo": "MULTICONCURSOS",
                        "nome": nome_salvar,
                        "qtd_concursos": qtd_concursos_sel,
                        "total_dezenas_unicas": len(dezenas_unicas_periodo),
                        "dezenas": dezenas_unicas_periodo,
                        "timestamp": hora_agora,
                        "status": "CONCLUÍDO & ATIVO",
                        "modo": tolerancia_multi,
                        "audit": audit_dados,
                        "pool_atualizado": carregar_pool_multi
                    }

                    st.success(f"Filtro para os últimos {qtd_concursos_sel} concursos ativado!")
                    st.rerun()

    else:
        with st.container(border=True):
            st.markdown("#### ⚡ ENGENHARIA REVERSA POR DEZENAS DIGITADAS")
            col_input_res, col_input_nome, col_input_tipo = st.columns([2.5, 1.8, 1.7])
            
            if "input_dezenas_digitadas_texto" not in st.session_state:
                st.session_state.input_dezenas_digitadas_texto = "10 17 42 43 57 59"

            with col_input_res:
                entrada_dezenas_filtro = st.text_area(
                    "Dezenas (6 a 60 números):",
                    value=st.session_state.input_dezenas_digitadas_texto,
                    height=75
                )
            with col_input_nome:
                nome_filtro_novo = st.text_input(
                    "Nome do Filtro:",
                    value="MEU_NOVO_FILTRO",
                    key="input_nome_filtro_auto"
                )
                substituir_pool_opcao = st.checkbox(
                    "Limpar Pool Anterior e Deixar Somente Estas Dezenas",
                    value=True
                )
            with col_input_tipo:
                tipo_tolerancia = st.selectbox(
                    "Nível de Tolerância:",
                    ["Perfil Flexível (Margem Aberta)", "Perfil Exato (Fiel à Amostra)"],
                    index=0,
                    key="select_modo_reverso"
                )

            c_btn_rev1, c_btn_rev2 = st.columns([2, 1])
            with c_btn_rev1:
                if st.button("⚡ GERAR, GRAVAR E ATIVAR FILTRO", type="primary", use_container_width=True):
                    nums_parse = [int(x) for x in re.findall(r"\b\d+\b", entrada_dezenas_filtro)]
                    dezenas_limpas = sorted(list(set([n for n in nums_parse if 1 <= n <= 60])))
                    total_identificado = len(dezenas_limpas)

                    if total_identificado < 6:
                        st.error(f"Informe pelo menos 6 dezenas válidas (entre 01 e 60). Identificadas: {total_identificado}.")
                    elif total_identificado > 60:
                        st.error(f"O limite máximo é 60 dezenas. Informadas: {total_identificado}.")
                    elif not nome_filtro_novo.strip():
                        st.error("Informe um nome para o filtro.")
                    else:
                        st.session_state.input_dezenas_digitadas_texto = " ".join([f"{n:02d}" for n in dezenas_limpas])
                        modo_sel = "exato" if tipo_tolerancia.startswith("Perfil Exato") else "flexivel"
                        preset_extraido = extrair_filtros_de_jogo(dezenas_limpas, modo=modo_sel)
                        nome_salvar = nome_filtro_novo.strip()

                        st.session_state.presets_filtros[nome_salvar] = preset_extraido
                        aplicar_preset(nome_salvar)

                        if substituir_pool_opcao:
                            st.session_state.pool_trabalho = set(dezenas_limpas)
                        else:
                            st.session_state.pool_trabalho = set(st.session_state.pool_trabalho) | set(dezenas_limpas)

                        hora_agora = time.strftime("%H:%M:%S - %d/%m/%Y")
                        st.session_state.linha_trabalho_reverso = {
                            "tipo": "AMOSTRA_DEZENAS",
                            "nome": nome_salvar,
                            "qtd_dezenas": total_identificado,
                            "dezenas": dezenas_limpas,
                            "timestamp": hora_agora,
                            "status": "PROCESSADO & ATIVO",
                            "modo": tipo_tolerancia,
                            "pool_atualizado": substituir_pool_opcao
                        }

                        st.success(f"Filtro '{nome_salvar}' ativado com sucesso para: {' - '.join([f'{n:02d}' for n in dezenas_limpas])}")
                        st.rerun()

            with c_btn_rev2:
                if st.button("🔄 Puxar Último Concurso", use_container_width=True):
                    if st.session_state.historico:
                        st.session_state.input_dezenas_digitadas_texto = " ".join([f"{n:02d}" for n in sorted(st.session_state.historico[-1])])
                        st.rerun()

    # Linha de Trabalho
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    if st.session_state.linha_trabalho_reverso:
        lt = st.session_state.linha_trabalho_reverso
        is_multi = lt.get("tipo") == "MULTICONCURSOS"
        dezenas_formatadas = " - ".join([f"{n:02d}" for n in sorted(lt["dezenas"])])

        if is_multi:
            detalhes_audit = (
                f"• Concursos Analisados: {lt['qtd_concursos']}<br>"
                f"• Dezenas Auditadas: {dezenas_formatadas}<br>"
                f"• Soma Observada: {lt['audit']['soma_min_real']} até {lt['audit']['soma_max_real']} | "
                f"Primos: {lt['audit']['primos_reais']} | Moldura: {lt['audit']['moldura_reais']}"
            )
        else:
            detalhes_audit = f"• Total de Dezenas: {lt['qtd_dezenas']}<br>• Dezenas: {dezenas_formatadas}"

        st.markdown(
            f'''
            <div style="background:#ffffff;border:4px solid #000000;border-radius:8px;padding:16px;margin-bottom:15px;">
                <div style="font-weight:900;color:#000000;font-size:16px;">
                    STATUS DA LINHA: {lt['status']} ({lt['nome']}) | 🕒 {lt['timestamp']}
                </div>
                <div style="margin-top:10px;font-size:14px;color:#000000;font-weight:800;line-height:1.7;">
                    {detalhes_audit}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    # Gerenciador de Predefinições
    with st.container(border=True):
        st.markdown("#### 💾 GERENCIADOR DE PREDEFINIÇÕES")
        col_puxar, col_gravar = st.columns(2)

        with col_puxar:
            lista_nomes = list(st.session_state.presets_filtros.keys())
            filtro_escolhido = st.selectbox("Carregar Filtro Salvo:", lista_nomes, index=0, key="select_preset_load")

            c_pux1, c_pux2 = st.columns(2)
            with c_pux1:
                if st.button("🚀 APLICAR PREDEFINIÇÃO", use_container_width=True):
                    aplicar_preset(filtro_escolhido)
                    st.success(f"Filtro '{filtro_escolhido}' carregado!")
                    st.rerun()
            with c_pux2:
                json_presets = json.dumps(st.session_state.presets_filtros, indent=2, ensure_ascii=False)
                st.download_button(
                    "💾 BAIXAR (.JSON)",
                    data=json_presets,
                    file_name="meus_filtros_mega60.json",
                    mime="application/json",
                    use_container_width=True
                )

        with col_gravar:
            nome_novo_filtro = st.text_input("Gravar Configuração Manual Atual:", placeholder="Ex: Meu Filtro 1", key="input_nome_filtro_manual")

            c_grv1, c_grv2 = st.columns(2)
            with c_grv1:
                if st.button("💾 GRAVAR MANUAL", use_container_width=True):
                    if not nome_novo_filtro.strip():
                        st.error("Informe um nome para a predefinição.")
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
                        st.success(f"Predefinição '{nome_novo_filtro.strip()}' gravada!")
                        st.rerun()
            with c_grv2:
                arq_json_upload = st.file_uploader("Importar (.JSON):", type=["json"], label_visibility="collapsed")
                if arq_json_upload is not None:
                    try:
                        st.session_state.presets_filtros.update(json.load(arq_json_upload))
                        st.success("Importado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao ler JSON: {e}")

        st.divider()
        opcoes_nomes = list(OPCOES_QUANTIDADE.keys())

        with st.container(border=True):
            st.markdown("#### 1️⃣ LINHAS INDIVIDUAIS (L01 a L06)")
            cols_l = st.columns(6)
            limites_linhas = []
            for r in range(6):
                with cols_l[r]:
                    val_padrao = st.session_state.get(f"sel_l_{r}", "0 a 2")
                    idx_sel = opcoes_nomes.index(val_padrao) if val_padrao in opcoes_nomes else 0
                    esc = st.selectbox(f"Linha {r+1:02d}", opcoes_nomes, index=idx_sel, key=f"sel_l_{r}")
                    limites_linhas.append(OPCOES_QUANTIDADE[esc])

        with st.container(border=True):
            st.markdown("#### 2️⃣ COLUNAS INDIVIDUAIS (C01 a C10)")
            cols_c_up, cols_c_dw = st.columns(5), st.columns(5)
            limites_colunas = []
            for c in range(10):
                alvo = cols_c_up[c] if c < 5 else cols_c_dw[c - 5]
                with alvo:
                    val_padrao = st.session_state.get(f"sel_c_{c}", "0 a 2")
                    idx_sel = opcoes_nomes.index(val_padrao) if val_padrao in opcoes_nomes else 0
                    esc = st.selectbox(f"Coluna {c+1:02d}", opcoes_nomes, index=idx_sel, key=f"sel_c_{c}")
                    limites_colunas.append(OPCOES_QUANTIDADE[esc])

        c_diag1, c_diag2 = st.columns(2)
        with c_diag1:
            with st.container(border=True):
                st.markdown("#### 3️⃣ DIAGONAIS CRESCENTES (DC01 a DC10 /)")
                with st.expander("Expandir Diagonais Crescentes", expanded=False):
                    limites_dc = []
                    for d in range(10):
                        val_padrao = st.session_state.get(f"sel_dc_{d}", "0 a 2")
                        idx_sel = opcoes_nomes.index(val_padrao) if val_padrao in opcoes_nomes else 0
                        esc = st.selectbox(f"DC{d+1:02d}", opcoes_nomes, index=idx_sel, key=f"sel_dc_{d}")
                        limites_dc.append(OPCOES_QUANTIDADE[esc])
        with c_diag2:
            with st.container(border=True):
                st.markdown("#### 4️⃣ DIAGONAIS DECRESCENTES (DD01 a DD10 \\)")
                with st.expander("Expandir Diagonais Decrescentes", expanded=False):
                    limites_dd = []
                    for d in range(10):
                        val_padrao = st.session_state.get(f"sel_dd_{d}", "0 a 2")
                        idx_sel = opcoes_nomes.index(val_padrao) if val_padrao in opcoes_nomes else 0
                        esc = st.selectbox(f"DD{d+1:02d}", opcoes_nomes, index=idx_sel, key=f"sel_dd_{d}")
                        limites_dd.append(OPCOES_QUANTIDADE[esc])

        with st.container(border=True):
            st.markdown("#### 5️⃣ PRIMOS, PARES, MOLDURA E FAIXA DE SOMA")
            c_p1, c_p2, c_p3, c_p4 = st.columns(4)
            with c_p1:
                primos_sel = st.multiselect("Quantidade de Primos:", list(range(7)), default=st.session_state.get("sel_primos", [3]), key="sel_primos")
            with c_p2:
                opcoes_par = {"3P / 3I": 3, "2P / 4I": 2, "4P / 2I": 4, "1P / 5I": 1, "5P / 1I": 5, "0P / 6I": 0, "6P / 0I": 6}
                par_sel = st.multiselect("Pares / Ímpares:", list(opcoes_par.keys()), default=st.session_state.get("sel_pares", ["2P / 4I"]), key="sel_pares")
                pares_valores = {opcoes_par[k] for k in par_sel}
            with c_p3:
                moldura_sel = st.multiselect("Dezenas na Moldura:", list(range(7)), default=st.session_state.get("sel_moldura", [5]), key="sel_moldura")
            with c_p4:
                val_soma_estado = st.session_state.get("sel_soma", (150, 190))
                if isinstance(val_soma_estado, (list, tuple)) and len(val_soma_estado) == 2:
                    soma_min_val = int(val_soma_estado[0])
                    soma_max_val = int(val_soma_estado[1])
                else:
                    soma_min_val, soma_max_val = 150, 190

                faixa_soma = st.slider(
                    "Faixa de Soma:",
                    min_value=50,
                    max_value=320,
                    value=(soma_min_val, soma_max_val),
                    key="sel_soma"
                )

        config_total = {
            "linhas": limites_linhas,
            "colunas": limites_colunas,
            "diag_cresc": limites_dc,
            "diag_decresc": limites_dd,
            "primos_aceitos": set(primos_sel),
            "pares_aceitos": pares_valores,
            "moldura_aceita": set(moldura_sel),
            "faixa_soma": faixa_soma
        }

        st.divider()

        st.markdown("#### ⚙️ CONTROLE DE EXECUÇÃO")
        c_ctrl1, c_ctrl2 = st.columns([2, 2])
        with c_ctrl1:
            sem_limite = st.checkbox(
                "♾️ SEM LIMITE (GERAR TODAS AS APROVADAS)",
                value=True
            )
        with c_ctrl2:
            if not sem_limite:
                teto_apostas = st.number_input(
                    "Teto Máximo de Jogos:",
                    min_value=1,
                    max_value=2000000,
                    value=5000,
                    step=500
                )
            else:
                teto_apostas = None
                st.info("Teto desativado: Todas as combinações válidas serão calculadas.")

        placeholder_metricas = st.empty()
        barra_progresso = st.progress(0, text="Pronto para processar...")

        pode_processar = len(st.session_state.pool_trabalho) >= 6

        col_btn_gen, col_btn_raw = st.columns(2)
        with col_btn_gen:
            if st.button("🚀 GERAR E FILTRAR APOSTAS", use_container_width=True, disabled=not pode_processar, type="primary"):
                if not primos_sel or not par_sel or not moldura_sel:
                    st.error("Selecione os parâmetros de Primos, Pares e Moldura.")
                else:
                    with st.spinner("🛠️ Processando Motor Combinatório..."):
                        t0 = time.time()
                        resultados = executar_varredura_pool(
                            st.session_state.pool_trabalho,
                            config_total,
                            barra_progresso,
                            placeholder_metricas,
                            teto_max=teto_apostas
                        )
                        t_fim = time.time() - t0
                        st.session_state.jogos_aprovados = resultados
                        total_gerado = len(resultados)

                        if total_gerado > 0:
                            st.success(f"✅ Sucesso: {total_gerado:,} apostas geradas em {t_fim:.2f}s.")
                        else:
                            st.warning(f"⚠️ Nenhuma combinação atendeu aos filtros selecionados em {t_fim:.2f}s.")

        with col_btn_raw:
            k_pool = len(st.session_state.pool_trabalho)
            comb_totais_pool = math.comb(k_pool, 6) if k_pool >= 6 else 0
            if st.button(f"📦 EXPORTAR POOL BRUTO ({comb_totais_pool:,} JOGOS)", use_container_width=True, disabled=not pode_processar):
                with st.spinner("Gerando arquivo..."):
                    dezenas_cands = sorted(list(st.session_state.pool_trabalho))
                    buffer_txt = io.StringIO()
                    for c in combinations(dezenas_cands, 6):
                        buffer_txt.write(" ".join([f"{n:02d}" for n in sorted(c)]) + "\n")
                    st.session_state["raw_pool_file"] = buffer_txt.getvalue()
                    st.success("Pool bruto gerado!")

        if "raw_pool_file" in st.session_state:
            st.download_button(
                "💾 BAIXAR ARQUIVO DO POOL BRUTO (.TXT)",
                data=st.session_state["raw_pool_file"],
                file_name=f"mega60_pool_bruto_{len(st.session_state.pool_trabalho)}dezenas.txt",
                mime="text/plain",
                use_container_width=True
            )

        if st.session_state.jogos_aprovados:
            qtd_aprov = len(st.session_state.jogos_aprovados)
            st.success(f"Total Aprovado: {qtd_aprov:,} apostas geradas (menor para o maior).")
            txt_saida = "\n".join([" ".join([f"{n:02d}" for n in sorted(j)]) for j in st.session_state.jogos_aprovados])

            c_d1, c_d2 = st.columns([3, 1])
            with c_d1:
                st.download_button(
                    "📥 BAIXAR JOGOS APROVADOS (.TXT)",
                    data=txt_saida,
                    file_name=f"mega60_apostas_filtradas_{qtd_aprov}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with c_d2:
                st.metric("Apostas Prontas", f"{qtd_aprov:,}")

# ==============================================================================
# ABA 3: VOLANTE VISUAL & RAIO-X
# ==============================================================================
with tab_volante:
    st.subheader("DISSECAÇÃO DA CARTELA")
    jogos_exibir = st.session_state.jogos_aprovados or st.session_state.jogos_upload

    if jogos_exibir:
        total_jogos = len(jogos_exibir)
        sel_idx = st.slider("Aposta para inspecionar:", 1, total_jogos, 1) if total_jogos > 1 else 1
        jogo_ativo = sorted(jogos_exibir[sel_idx - 1])
        marcadas = set(jogo_ativo)

        c_v1, c_v2 = st.columns([1, 1])
        with c_v1:
            celulas = ""
            for r in range(6):
                for c in range(10):
                    n = r * 10 + c + 1
                    if n in marcadas:
                        celulas += f'<div style="width:42px;height:42px;background:#facc15;color:#000000;border:3px solid #000000;font-weight:900;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:16px;">{n:02d}</div>'
                    else:
                        celulas += f'<div style="width:42px;height:42px;background:#ffffff;color:#000000;border:1px solid #000000;font-weight:900;border-radius:6px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:16px;">{n:02d}</div>'

            html_cartela = f'''
            <!DOCTYPE html><html><head><meta charset="utf-8">
            <style>*{{box-sizing:border-box;}}body{{margin:0;padding:0;display:flex;justify-content:center;background:transparent;font-family:Arial,sans-serif;}}
            .box{{background:#fff;border:4px solid #000000;border-radius:10px;padding:12px;width:fit-content;}}
            .grid{{display:grid;grid-template-columns:repeat(10,42px);gap:5px;}}</style></head><body>
            <div class="box"><div style="font-weight:900;font-size:16px;margin-bottom:10px;color:#000000;text-align:center;">JOGO #{sel_idx:04d}: {" - ".join([f"{n:02d}" for n in jogo_ativo])}</div>
            <div class="grid">{celulas}</div></div></body></html>
            '''
            render_html_seguro(html_cartela, 360)

        with c_v2:
            with st.container(border=True):
                st.markdown("#### 🔬 RAIO-X DO JOGO")
                cnt_linhas = Counter(PROPS[n]["r"] + 1 for n in jogo_ativo)
                cnt_colunas = Counter(PROPS[n]["c"] + 1 for n in jogo_ativo)
                cnt_dc = Counter(PROPS[n]["dc"] + 1 for n in jogo_ativo)
                cnt_dd = Counter(PROPS[n]["dd"] + 1 for n in jogo_ativo)

                st.markdown("**Linhas:** " + " • ".join([f"L{k}: **{v}x**" for k, v in sorted(cnt_linhas.items())]))
                st.markdown("**Colunas:** " + " • ".join([f"C{k:02d}: **{v}x**" for k, v in sorted(cnt_colunas.items())]))
                st.markdown("**Diagonais Cresc.:** " + " • ".join([f"DC{k:02d}: **{v}x**" for k, v in sorted(cnt_dc.items())]))
                st.markdown("**Diagonais Decresc.:** " + " • ".join([f"DD{k:02d}: **{v}x**" for k, v in sorted(cnt_dd.items())]))

                pr = sum(1 for n in jogo_ativo if PROPS[n]["is_primo"])
                pa = sum(1 for n in jogo_ativo if PROPS[n]["is_par"])
                mo = sum(1 for n in jogo_ativo if PROPS[n]["is_moldura"])
                st.divider()
                st.markdown(f"**Pares/Ímpares:** `{pa}P / {6-pa}I` | **Primos:** `{pr}` | **Moldura:** `{mo}` | **Soma:** `{sum(jogo_ativo)}`")
    else:
        st.info("Gere apostas para inspecionar no volante.")

# ==============================================================================
# ABA 4: UPLOAD & FILTRAGEM SUCESSIVA
# ==============================================================================
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
                        t_ini_flt = time.time()
                        aprovados_do_arquivo = [
                            j for j in jogos_up if validar_aposta_final_6(tuple(j), config_total)
                        ]
                        t_fim_flt = time.time() - t_ini_flt
                        st.session_state.jogos_filtrados_upload = aprovados_do_arquivo
                        st.success(f"Concluído em {t_fim_flt:.2f}s! {len(aprovados_do_arquivo):,} de {total_up:,} aprovadas.")

            if st.session_state.jogos_filtrados_upload:
                qtd_flt = len(st.session_state.jogos_filtrados_upload)
                txt_flt = "\n".join([" ".join([f"{n:02d}" for n in sorted(j)]) for j in st.session_state.jogos_filtrados_upload])
                with c_flt2:
                    st.download_button(
                        f"💾 BAIXAR LOTE FILTRADO ({qtd_flt:,} JOGOS)",
                        data=txt_flt,
                        file_name=f"mega60_lote_filtrado_{qtd_flt}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

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

            html_up = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box;}}body{{margin:0;padding:0;background:transparent;display:flex;justify-content:center;font-family:Arial,sans-serif;}}.box{{background:#fff;border:4px solid #000000;border-radius:10px;padding:10px;width:fit-content;}}.grid{{display:grid;grid-template-columns:repeat(10,40px);gap:4px;}}</style></head><body><div class="box"><div class="grid">{celulas_up_heat}</div></div></body></html>'
            render_html_seguro(html_up, 310)

        with col_conf_right:
            st.markdown("### 🎯 CONFERÊNCIA DE RESULTADOS")
            ult_sorteio = st.session_state.historico[-1] if st.session_state.historico else [4, 12, 18, 30, 35, 54]
            txt_padrao = " ".join([f"{n:02d}" for n in sorted(ult_sorteio)])

            modo_origem = st.radio("Origem:", ["Último Sorteio Oficial", "Digitar Manualmente"], horizontal=True)
            if modo_origem == "Último Sorteio Oficial":
                dezenas_conf = sorted(ult_sorteio)
            else:
                entrada_manual = st.text_input("6 Dezenas Sorteadas:", value=txt_padrao)
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
                    st.success(f"{tot_prem} aposta(s) premiada(s) encontradas!")
                    jogos_premiados_txt = "\n".join([
                        f"{' '.join([f'{n:02d}' for n in it['jogo']])} | {it['qtd_acertos']} ACERTOS"
                        for it in relatorio_conf if it["qtd_acertos"] >= 4
                    ])
                    st.download_button(
                        "📥 BAIXAR APOSTAS PREMIADAS (.TXT)",
                        data=jogos_premiados_txt,
                        file_name=f"mega60_apostas_premiadas_{tot_prem}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("Nenhuma aposta alcançou 4, 5 ou 6 acertos.")

                jogos_com_acerto = [it for it in relatorio_conf if it["qtd_acertos"] >= 4] or relatorio_conf
                opcoes_map = {
                    it["num_aposta"]: f"Aposta #{it['num_aposta']:04d} — {it['qtd_acertos']} acertos"
                    for it in jogos_com_acerto[:50]
                }
                idx_escolhido = st.selectbox(
                    "Inspecionar no Volante:",
                    list(opcoes_map.keys()),
                    format_func=lambda x: opcoes_map[x]
                )
                if idx_escolhido is not None:
                    item_ativo = next(it for it in relatorio_conf if it["num_aposta"] == idx_escolhido)
                    render_volante_conferencia(
                        item_ativo["jogo"],
                        dezenas_conf,
                        titulo=f"Aposta #{item_ativo['num_aposta']:04d} ({item_ativo['qtd_acertos']} Acertos)"
                    )
    else:
        st.info("Carregue um arquivo para conferência.")

# ==============================================================================
# ABA 5: HISTÓRICO & API CAIXA
# ==============================================================================
with tab_historico:
    st.subheader("BASE DE CONCURSOS OFICIAIS")
    st.markdown(f"**Total em memória:** `{len(st.session_state.historico)}` ({st.session_state.origem})")

    if st.button("🌐 SINCRONIZAR COM A CAIXA AGORA", type="primary"):
        with st.spinner("Conectando..."):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://loterias.caixa.gov.br/"
                }
                r = requests.get(
                    "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena",
                    headers=headers,
                    timeout=10,
                    verify=False
                )
                if r.status_code == 200:
                    ult = r.json()
                    dezenas_sorteadas = sorted([int(x) for x in ult.get("listaDezenas", [])])

                    if len(dezenas_sorteadas) == 6:
                        if dezenas_sorteadas not in st.session_state.historico:
                            st.session_state.historico.append(dezenas_sorteadas)
                        st.session_state.origem = f"API Caixa (Concurso #{ult.get('numero', '?')})"
                        st.session_state.input_resultado_reverso_val = " ".join([f"{n:02d}" for n in dezenas_sorteadas])
                        st.success(f"Concurso #{ult.get('numero')} sincronizado: {' - '.join([f'{n:02d}' for n in dezenas_sorteadas])}")
                        st.rerun()
                    else:
                        st.warning("Formato inesperado.")
                else:
                    st.warning(f"Erro HTTP {r.status_code}.")
            except Exception as e:
                st.error(f"Erro: {e}")

    with st.expander("Ver Concursos Armazenados"):
        for i, sorteio in enumerate(reversed(st.session_state.historico), start=1):
            st.markdown(f"**Concurso #{i:02d}:** `{' - '.join([f'{n:02d}' for n in sorted(sorteio)])}`")
