# =====================================
# app.py – Painel IQE Completo (Parte 1/3)
# =====================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ============================
# CONFIGURAÇÕES GERAIS
# ============================
st.set_page_config(
    page_title="Painel IQE – Pós-graudação em Mineração de Dados Educacionais - IFES",
    page_icon="📊",
    layout="wide"
)

# ============================
# ESTILOS GERAIS
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; color:#5F6169; }

/* Cards */
.big-card{background:#3A0057;color:#fff;padding:28px;border-radius:14px;text-align:center;box-shadow:0 0 12px rgba(0,0,0,.15);}
.small-card,.white-card{padding:22px;border-radius:12px;text-align:center;border:1px solid #E0E0E0;box-shadow:0 0 6px rgba(0,0,0,.08);}
.small-card{background:#F3F3F3;color:#3A0057;}
.white-card{background:#fff;color:#3A0057;}

/* Abas */
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
  background:#fff; color:#3A0057; border:1px solid #E5D9EF;
  border-radius:10px; padding:10px 16px;
}
.stTabs [aria-selected="true"] { background:#3A0057 !important; color:#fff !important; }

/* Centraliza tabela */
.dataframe td, .dataframe th {
  text-align: center !important;
  vertical-align: middle !important;
}
</style>
""", unsafe_allow_html=True)

# ============================
# SIDEBAR PRINCIPAL
# ============================
import os

try:
    logo_path = os.path.join("assets", "logotipo_zetta_branco.png")
    st.sidebar.image(logo_path, use_container_width=True)
except Exception:
    st.sidebar.markdown("### 🟣 Pós-graudação em Mineração de Dados Educacionais - IFES")
st.sidebar.title("Navegação")

menu = st.sidebar.radio(
    "Escolha a seção:",
    ["📘 Entenda o ICMS Educacional", "📊 IQE"],
    index=0
)

# ============================
# SEÇÃO 1 – ENTENDA O ICMS EDUCACIONAL
# ============================
if menu == "📘 Entenda o ICMS Educacional":
    st.title("📘 Entenda o ICMS Educacional do Espírito Santo")

    st.markdown("""
    **Tabela 1** – Ano de aplicação do Paebes, ano de cálculo do IQE,
    ano dos repasses financeiros aos municípios e percentual do ICMS referente à educação em cada ano.
    """)

    dados_icms = pd.DataFrame({
        "Edição do PAEbes de ref. para melhoria": [2022, 2023, 2024, 2025],
        "Edição do PAEbes ref. para o resultado": [2023, 2024, 2025, 2026],
        "Ano de cálculo do IQE": [2024, 2025, 2026, 2027],
        "Ano de repasse do ICMS": [2025, 2026, 2027, 2028],
        "Peso do IQE no repasse do ICMS": ["10%", "12%", "12,5%", "12,5%"]
    })

    st.dataframe(dados_icms, use_container_width=True, hide_index=True)
    st.caption("Fonte: SEDU/ES")

# ============================
# SEÇÃO 2 – PAINEL IQE
# ============================
elif menu == "📊 IQE":

    # ===== CARREGAMENTO DE DADOS =====
    @st.cache_data(show_spinner=True)
    def carregar_dados():
        caminho = "data/IQE_Painel_Modelo - 19102025.xlsx"
        base = pd.read_excel(caminho, sheet_name="Base_Painel")
        dim = pd.read_excel(caminho, sheet_name="Dim_Indicador")

        def _coerce_num(col):
            if pd.api.types.is_numeric_dtype(col): 
                return col
            col = col.astype(str).str.strip().replace(
                {"-": np.nan, "--": np.nan, "—": np.nan, "nan": np.nan, "None": np.nan, "": np.nan}
            )
            col = col.str.replace(",", ".", regex=False)
            return pd.to_numeric(col, errors="ignore")

        base = base.apply(_coerce_num)
        for c in ["IQE","IQEF","P","IMEG"]:
            if c in base.columns:
                base[c] = pd.to_numeric(base[c], errors="coerce")

        if "Ano-Referência" in base.columns:
            base["Ano-Referência"] = pd.to_numeric(base["Ano-Referência"], errors="coerce")
        return base, dim

    base, dim = carregar_dados()

    # ===== SIDEBAR DO PAINEL =====
    st.sidebar.title("Painel IQE – Municípios")
    municipios = sorted(base["Município"].astype(str).unique())
    municipio_sel = st.sidebar.selectbox("Selecione o município:", municipios)

    anos = sorted([a for a in base["Ano-Referência"].dropna().unique()])
    if len(anos) >= 2:
        ano_anterior, ano_atual = anos[-2], anos[-1]
    else:
        ano_anterior = ano_atual = anos[-1]
    edicao_anterior, edicao_atual = ano_anterior + 1, ano_atual + 1

    dados_atual = base.loc[base["Ano-Referência"] == ano_atual].copy()
    dados_ant  = base.loc[base["Ano-Referência"] == ano_anterior].copy()

    def valor_municipio(df, indicador, default=np.nan):
        try:
            v = df.loc[df["Município"] == municipio_sel, indicador].values
            return float(v[0]) if len(v) else default
        except Exception:
            return default

    def ranking(df, coluna):
        df = df[["Município", coluna]].dropna().sort_values(coluna, ascending=False).reset_index(drop=True)
        if municipio_sel in df["Município"].tolist():
            pos = int(df.index[df["Município"] == municipio_sel][0] + 1)
            return pos, len(df)
        return None, len(df)

    # ===== ABAS =====
    tab_resumo, tab_decomp, tab_iqef, tab_evol_eq, tab_tend, tab_fundeb, tab_sim = st.tabs([
        "📊 Resumo Geral",
        "⚙️ Decomposição IQE",
        "📘 IQEF e IMEG Detalhados",
        "📈 Evolução & Equidade",
        "📉 Tendência",
        "💰 Fundeb",
        "🧮 Simulador"
    ])

    # ---------------------------------------------------------
    # 1️⃣ RESUMO GERAL
    # ---------------------------------------------------------
    with tab_resumo:
        st.title(f"📊 Resumo Geral – {municipio_sel}")

        iqe_atual = valor_municipio(dados_atual, "IQE")
        iqe_anterior = valor_municipio(dados_ant, "IQE")
        media_estadual = float(pd.to_numeric(dados_atual["IQE"], errors="coerce").mean())

        rank_atual, total_mun = ranking(dados_atual, "IQE")
        rank_ant, _ = ranking(dados_ant, "IQE")

        if rank_atual and rank_ant:
            delta = rank_ant - rank_atual
            if delta > 0:
                texto_rank = f"{rank_atual}º / {total_mun}  <span style='color:green;'>📈 ↑ {delta} posições</span>"
            elif delta < 0:
                texto_rank = f"{rank_atual}º / {total_mun}  <span style='color:red;'>📉 ↓ {abs(delta)} posições</span>"
            else:
                texto_rank = f"{rank_atual}º / {total_mun} (sem variação)"
        elif rank_atual:
            texto_rank = f"{rank_atual}º / {total_mun} (sem dado anterior)"
        else:
            texto_rank = "Sem ranking para este município"

        col1, col2 = st.columns([1.25,1])
        with col1:
            st.markdown(f"""
            <div class="big-card">
                <h3>IQE {int(edicao_atual - 1)}</h3>
                <h1 style='font-size:48px;margin-top:-8px;'>{(iqe_atual if np.isfinite(iqe_atual) else np.nan):.3f}</h1>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="small-card">
                <h4>IQE {int(edicao_anterior - 1)}</h4>
                <h2 style='margin-top:-5px;'>{(iqe_anterior if np.isfinite(iqe_anterior) else np.nan):.3f}</h2>
            </div>
            """, unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"""
            <div class="white-card">
                <h4>Média Estadual ({int(edicao_atual - 1)})</h4>
                <h2 style='margin-top:-5px;'>{media_estadual:.3f}</h2>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="white-card">
                <h4>Ranking Atual ({int(edicao_atual - 1)})</h4>
                <h2 style='margin-top:-5px;'>{texto_rank}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown(
            "<p style='text-align:center;color:#5F6169;'>Painel desenvolvido por <b>Zetta Inteligência em Dados</b></p>",
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # 2️⃣ DECOMPOSIÇÃO IQE (Comparativo 2023 × 2024)
    # ---------------------------------------------------------
    with tab_decomp:
        st.subheader("⚙️ Decomposição IQE – Comparativo 2023 × 2024")

        componentes = ["IQEF", "P", "IMEG"]
        pesos = {"IQEF": 0.70, "P": 0.15, "IMEG": 0.15}
        anos_comparar = [2023, 2024]

        cores_barras = {2023: "rgba(194,164,207,0.35)", 2024: "rgba(58,0,87,0.25)"}
        cores_mun    = {2023: "#A57DBB", 2024: "#3A0057"}
        cores_media  = {2023: "#7D4E9F", 2024: "#C8AADC"}

        dados_comp = base.copy()
        dados_comp["Ano-Referência"] = pd.to_numeric(dados_comp["Ano-Referência"], errors="coerce")
        dados_comp = dados_comp[dados_comp["Ano-Referência"].isin(anos_comparar)].copy()
        # --- Long format
        df_long = (
            dados_comp[["Município", "Ano-Referência"] + componentes]
            .melt(id_vars=["Município", "Ano-Referência"], var_name="Componente", value_name="Valor")
        )

        # --- Estatísticas
        resumo = (
            df_long.groupby(["Componente", "Ano-Referência"], as_index=False)
            .agg(media=("Valor", "mean"), minimo=("Valor", "min"), maximo=("Valor", "max"))
        )

        # --- Valores do município
        valores_mun = []
        for ano in anos_comparar:
            for c in componentes:
                try:
                    v = float(
                        dados_comp.loc[
                            (dados_comp["Município"] == municipio_sel)
                            & (dados_comp["Ano-Referência"] == ano),
                            c
                        ].values[0]
                    )
                except Exception:
                    v = np.nan
                valores_mun.append({"Componente": c, "Ano-Referência": ano, "municipio": v})
        resumo = resumo.merge(pd.DataFrame(valores_mun), on=["Componente", "Ano-Referência"], how="left")

        # --- Ordem e rótulos
        ordem_labels = []
        for comp in componentes:
            for ano in [2023, 2024]:
                ordem_labels.append(f"{comp} ({int(pesos[comp]*100)}%) – {ano}")

        labels_em_ordem = list(reversed(ordem_labels))
        y_pos_map = {lab: i for i, lab in enumerate(labels_em_ordem)}
        resumo["label"] = resumo.apply(
            lambda r: f"{r['Componente']} ({int(pesos[r['Componente']]*100)}%) – {r['Ano-Referência']}",
            axis=1
        )
        resumo["ypos"] = resumo["label"].map(y_pos_map)

        # --- Gráfico
        fig = go.Figure()

        # Barras Min–Máx
        for ano in anos_comparar:
            sub = resumo[resumo["Ano-Referência"] == ano]
            for _, r in sub.iterrows():
                fig.add_trace(go.Bar(
                    y=[r["ypos"]],
                    x=[r["maximo"] - r["minimo"]],
                    base=r["minimo"],
                    orientation="h",
                    marker_color=cores_barras[ano],
                    name=f"Faixa (mín–máx) {ano}",
                    showlegend=False,
                    width=0.9
                ))

        # --- Configurações de deslocamento
        desloc_padrao = 0.18
        lim_proximidade = 0.025

        # --- Marcadores
        for ano in anos_comparar:
            sub = resumo[resumo["Ano-Referência"] == ano].copy()

            # Município (quadrado + valor)
            fig.add_trace(go.Scatter(
                y=sub["ypos"],
                x=sub["municipio"],
                mode="markers+text",
                marker=dict(symbol="square", size=10, color=cores_mun[ano]),
                text=[f"{v:.3f}" if pd.notna(v) else "" for v in sub["municipio"]],
                textposition="middle right",
                textfont=dict(size=12, color=cores_mun[ano]),
                name=f"Município ({ano})",
                hoverinfo="text",
                hovertext=[f"Município ({ano}): {v:.3f}" if pd.notna(v) else "" for v in sub["municipio"]],
            ))

            # Média Estadual (losango) — deslocamento vertical fixo
            y_media = []
            for _, r in sub.iterrows():
                m = r["media"]
                v = r["municipio"]
                if pd.isna(m) or pd.isna(v):
                    y_media.append(r["ypos"])
                    continue
                diff = abs(v - m)
                if diff <= lim_proximidade:
                    y_media.append(r["ypos"] - desloc_padrao)
                else:
                    y_media.append(r["ypos"])

            fig.add_trace(go.Scatter(
                y=y_media,
                x=sub["media"],
                mode="markers",
                marker=dict(symbol="diamond", size=11, color=cores_media[ano]),
                name=f"Média Estadual ({ano})",
                hoverinfo="text",
                hovertext=[f"Média estadual ({ano}): {m:.3f}" if pd.notna(m) else "" for m in sub["media"]],
            ))

        fig.update_layout(
            height=580,
            template="simple_white",
            xaxis=dict(range=[0, 1.05], title="Valor", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
            yaxis=dict(
                title="",
                tickmode="array",
                tickvals=list(range(len(labels_em_ordem))),
                ticktext=labels_em_ordem
            ),
            title=f"Comparação por componente — {municipio_sel} (2023 × 2024)",
            legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0.02),
            margin=dict(t=90, b=40, l=40, r=40),
            bargap=0.15,
            bargroupgap=0.05,
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
    
            "<p style='text-align:center;color:#5F6169;'>Fonte: Base Painel IQE (2023–2024) – Zetta Inteligência em Dados</p>",
            unsafe_allow_html=True
        )

        # ---------------------------------------------------------
    # 3️⃣ IQEF DETALHADO – Radar + Barras ΔDESVFSEt
    # ---------------------------------------------------------
    with tab_iqef:
        st.subheader("📘 Detalhamento – Desempenho nos Indicadores")

        # Seletor IQEF ou IMEG
        modo_radar = st.radio(
            "O que você quer ver no radar?",
            ["IQEF", "IMEG"],
            horizontal=True,
            key="radar_tipo"
        )

        # Base do ano atual
        dados_ano = base.loc[base["Ano-Referência"] == ano_atual].copy()
        for col in dados_ano.columns:
            if col not in ["Município", "Ano-Referência"]:
                dados_ano[col] = pd.to_numeric(dados_ano[col], errors="ignore")

        # Radar IQEF
        if modo_radar == "IQEF":
            indicadores_iqef = [
                "IQ2","IQ5",
                "IDE2","IDE5","PMNLP2","PMNMT2","PMNLP5","PMNMT5",
                "IDALP2","IDAMT2","IDALP5","IDAMT5",
                "TPLP2","TPMT2","TPLP5","TPMT5"
            ]
            cols_radar = [c for c in indicadores_iqef if c in dados_ano.columns]
            st.markdown("### 🌐 Radar – IQEF (IDE, PMN, IDA, TP)")
        else:
            indicadores_imeg = ["IVEC", "IEQLP2", "IEQMT2", "IEQLP5", "IEQMT5"]
            cols_radar = [c for c in indicadores_imeg if c in dados_ano.columns]
            st.markdown("### 🌐 Radar – IMEG (IVEC e IEQs)")

        if not cols_radar or municipio_sel not in dados_ano["Município"].tolist():
            st.warning("Não encontrei indicadores suficientes para gerar o radar.")
        else:
            for c in cols_radar:
                dados_ano[c] = pd.to_numeric(dados_ano[c], errors="coerce")

            linha_mun = dados_ano.loc[dados_ano["Município"] == municipio_sel, cols_radar].iloc[0]
            media_est = dados_ano[cols_radar].mean()

            categorias = cols_radar[:] + [cols_radar[0]]
            valores_mun = linha_mun.tolist() + [linha_mun.tolist()[0]]
            valores_med = media_est.tolist() + [media_est.tolist()[0]]

            fig_radar = go.Figure()

            # Média Estadual – verde-azulado (contraste com roxo)
            fig_radar.add_trace(go.Scatterpolar(
                r=valores_med,
                theta=categorias,
                fill='toself',
                name='Média Estadual',
                line=dict(color='#00A3A3', width=2),
                fillcolor='rgba(0,163,163,0.30)'
            ))

            # Município – roxo escuro
            fig_radar.add_trace(go.Scatterpolar(
                r=valores_mun,
                theta=categorias,
                fill='toself',
                name=municipio_sel,
                line=dict(color='#3A0057', width=2),
                fillcolor='rgba(58,0,87,0.40)'
            ))

            # Layout geral
            fig_radar.update_layout(
                title=f"{municipio_sel} × Média Estadual ({int(edicao_atual)}) – Indicadores {modo_radar}",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        gridcolor='rgba(0,0,0,0.08)'
                    )
                ),
                showlegend=True,
                legend=dict(
                    orientation='h',
                    y=-0.15,
                    x=0.25
                ),
                height=540,
                font=dict(family='Montserrat', size=12, color='#3A0057'),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            st.plotly_chart(fig_radar, use_container_width=True)

        # BARRAS ΔDESVFSEt
        st.markdown("### 📊 ΔDESVFSEt – Variações de Desempenho (2º e 5º anos)")
        indicadores_barras = ["ΔDESVFSEtLP2", "ΔDESVFSEtMT2", "ΔDESVFSEtLP5", "ΔDESVFSEtMT5"]
        existentes = [c for c in indicadores_barras if c in dados_ano.columns]

        if not existentes:
            st.info("Sem dados suficientes para ΔDESVFSEt.")
        else:
            linhas = []
            for ind in existentes:
                med = float(pd.to_numeric(dados_ano[ind], errors="coerce").mean())
                try:
                    v = float(dados_ano.loc[dados_ano["Município"] == municipio_sel, ind].values[0])
                except Exception:
                    v = np.nan
                linhas.append({"Indicador": ind, "Município": v, "Média Estadual": med})
            df_barras = pd.DataFrame(linhas).dropna(subset=["Município", "Média Estadual"], how="all")

            fig_barras = go.Figure()
            fig_barras.add_trace(go.Bar(
                y=df_barras["Indicador"],
                x=df_barras["Município"],
                name="Município",
                orientation="h",
                marker_color="#3A0057",
                text=[f"{v:.3f}" for v in df_barras["Município"]],
                textposition="outside"
            ))
            fig_barras.add_trace(go.Bar(
                y=df_barras["Indicador"],
                x=df_barras["Média Estadual"],
                name="Média Estadual",
                orientation="h",
                marker_color="#C2A4CF",
                text=[f"{v:.3f}" for v in df_barras["Média Estadual"]],
                textposition="outside"
            ))
            fig_barras.update_layout(
                barmode="group",
                xaxis=dict(range=[0, 1], title="Valor"),
                yaxis=dict(title="Indicador"),
                height=480,
                font=dict(family="Montserrat", size=12, color="#3A0057"),
                legend=dict(orientation="h", y=1.02, x=0)
            )
            st.plotly_chart(fig_barras, use_container_width=True)

    # ---------------------------------------------------------
    # 4️⃣ EVOLUÇÃO & EQUIDADE – IQE linha + ΔIDEN barras
    # ---------------------------------------------------------
    with tab_evol_eq:
        st.subheader("📈 Evolução & Equidade – IQE e ΔIDEN")

        dados_t = base.copy()
        dados_t["IQE"] = pd.to_numeric(dados_t.get("IQE", np.nan), errors="coerce")
        dados_t["Ano-Referência"] = pd.to_numeric(dados_t["Ano-Referência"], errors="coerce")
        dados_t = dados_t.dropna(subset=["IQE","Ano-Referência"])
        hist_mun = dados_t.loc[dados_t["Município"] == municipio_sel].sort_values("Ano-Referência")

        if hist_mun.empty:
            st.warning("Não há dados de IQE suficientes para evolução.")
        else:
            estat = (dados_t.groupby("Ano-Referência", as_index=False)
                     .agg(Média=("IQE","mean"), Mín=("IQE","min"), Máx=("IQE","max")))
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=hist_mun["Ano-Referência"], y=hist_mun["IQE"],
                                      mode="lines+markers", name=municipio_sel,
                                      line=dict(color="#3A0057", width=3), marker=dict(size=8)))
            fig1.add_trace(go.Scatter(x=estat["Ano-Referência"], y=estat["Média"], mode="lines+markers",
                                      name="Média Estadual", line=dict(color="#C2A4CF", dash="dash")))
            fig1.add_trace(go.Scatter(x=estat["Ano-Referência"], y=estat["Mín"],
                                      mode="lines", name="Mínimo Estadual", line=dict(color="#AAAAAA", dash="dot")))
            fig1.add_trace(go.Scatter(x=estat["Ano-Referência"], y=estat["Máx"],
                                      mode="lines", name="Máximo Estadual", line=dict(color="#AAAAAA", dash="dot")))
            fig1.update_layout(title=f"Evolução do IQE ({municipio_sel})", xaxis_title="Ano de Referência",
                               yaxis_title="IQE", yaxis=dict(range=[0,1]), height=420,
                               plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="Montserrat", size=12, color="#3A0057"))
            st.plotly_chart(fig1, use_container_width=True)

        st.markdown("#### ΔIDEN – Comparativo entre edições (2023 e 2024)")
        cols_delta = [c for c in ["DeltaIDEN2","DeltaIDEN5"] if c in base.columns]
        if len(anos) >= 2 and cols_delta:
            def deltas(ano_ref):
                df = base.loc[base["Ano-Referência"] == ano_ref]
                return [valor_municipio(df, c) for c in cols_delta]

            v_2023 = deltas(2023)
            v_2024 = deltas(2024)

            x = cols_delta
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=x, y=v_2023, name="Edição 2023", marker_color="#C2A4CF"))
            fig2.add_trace(go.Bar(x=x, y=v_2024, name="Edição 2024", marker_color="#3A0057"))
            fig2.update_layout(barmode="group", yaxis=dict(range=[0,1]),
                               xaxis_title="Indicador de Equidade", yaxis_title="Valor (ΔIDEN)",
                               height=420, plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="Montserrat", size=12, color="#3A0057"))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Não há colunas ΔIDEN suficientes para o comparativo 2023 × 2024.")

    # ---------------------------------------------------------
    # 5️⃣ TENDÊNCIA
    # ---------------------------------------------------------
    with tab_tend:
        st.subheader("📉 Tendência do IQE ao longo dos anos")
        if hist_mun.empty:
            st.warning("Sem dados históricos suficientes para análise de tendência.")
        else:
            z = np.polyfit(hist_mun["Ano-Referência"], hist_mun["IQE"], 1)
            p = np.poly1d(z)
            tendencia = p(hist_mun["Ano-Referência"])

            fig_tend = go.Figure()
            fig_tend.add_trace(go.Scatter(x=hist_mun["Ano-Referência"], y=hist_mun["IQE"],
                                          mode="markers+lines", name="IQE Observado",
                                          line=dict(color="#3A0057", width=2)))
            fig_tend.add_trace(go.Scatter(x=hist_mun["Ano-Referência"], y=tendencia,
                                          mode="lines", name="Tendência Linear",
                                          line=dict(color="#C2A4CF", dash="dash")))
            fig_tend.update_layout(height=420, template="simple_white",
                                   xaxis_title="Ano de Referência", yaxis_title="IQE",
                                   font=dict(family="Montserrat", size=12, color="#3A0057"))
            st.plotly_chart(fig_tend, use_container_width=True)

    # ---------------------------------------------------------
    # 6️⃣ FUNDEB – RELAÇÃO IQE E FINANCIAMENTO
    # ---------------------------------------------------------
    with tab_fundeb:
        st.subheader("💰 Fundeb e ICMS Educacional")

        st.markdown("""
        O **ICMS Educacional** influencia diretamente os repasses financeiros aos municípios,
        e o **IQE** é um dos principais componentes dessa distribuição.
        A correlação entre desempenho educacional e recursos financeiros é um incentivo
        para o aprimoramento contínuo das políticas públicas de educação.
        """)

        if hist_mun.empty:
            st.info("Sem dados históricos suficientes para gerar análise financeira.")
        else:
            df_fundeb = hist_mun.copy()
            df_fundeb["ICMS_Educacional_estimado"] = df_fundeb["IQE"] * 100  # proxy ilustrativa

            fig_fundeb = go.Figure()
            fig_fundeb.add_trace(go.Bar(x=df_fundeb["Ano-Referência"], y=df_fundeb["ICMS_Educacional_estimado"],
                                        name="ICMS Educacional (estimado)", marker_color="#3A0057"))
            fig_fundeb.add_trace(go.Scatter(x=df_fundeb["Ano-Referência"], y=df_fundeb["IQE"]*100,
                                            name="IQE (×100)", yaxis="y2", line=dict(color="#C2A4CF", width=3)))
            fig_fundeb.update_layout(
                title=f"{municipio_sel} – Relação entre IQE e ICMS Educacional (estimado)",
                xaxis=dict(title="Ano de Referência"),
                yaxis=dict(title="ICMS Educacional (escala relativa)"),
                yaxis2=dict(title="IQE (×100)", overlaying="y", side="right"),
                height=420,
                template="simple_white",
                font=dict(family="Montserrat", size=12, color="#3A0057")
            )
            st.plotly_chart(fig_fundeb, use_container_width=True)

    # ---------------------------------------------------------
    # 7️⃣ SIMULADOR
    # ---------------------------------------------------------
    with tab_sim:
        st.subheader("🧮 Simulador de Cenários – IQE e Impactos")

        st.markdown("""
        Ajuste os valores abaixo para simular possíveis cenários futuros e observar como eles
        poderiam afetar o **Índice de Qualidade da Educação (IQE)** do município.
        """)

        col1, col2, col3 = st.columns(3)
        iqef = col1.slider("IQEF (70%)", 0.0, 1.0, 0.7, 0.01)
        p = col2.slider("P (15%)", 0.0, 1.0, 0.5, 0.01)
        imeg = col3.slider("IMEG (15%)", 0.0, 1.0, 0.6, 0.01)

        iqe_simulado = iqef*0.7 + p*0.15 + imeg*0.15
        st.metric(label="IQE Simulado", value=f"{iqe_simulado:.3f}")

        st.markdown("---")
        st.caption("Simulação ilustrativa – não representa cálculo oficial do IQE.")

# ---------------------------------------------------------
# RODAPÉ
# ---------------------------------------------------------
st.markdown(
    """
    <hr style='margin-top:40px;'>
    <div style='text-align:center; color:#7E7E7E; font-size:13px;'>
        Desenvolvido por <b>Zetta Inteligência em Dados</b> · Painel Educacional <b>IQE ES</b> · 2025
    </div>
    """,
    unsafe_allow_html=True
)






