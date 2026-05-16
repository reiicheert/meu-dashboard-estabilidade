import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. Configuração da Interface Executiva
st.set_page_config(page_title="Global Stability Monitor", layout="wide")

st.title("📊 Global Stability Index Analysis")
st.markdown("""
Monitoramento estratégico de indicadores de fragilidade estatal e riscos geopolíticos.
*Base de dados institucional pré-carregada para análise consultiva.*
""")

# --- LÓGICA DE CARREGAMENTO AUTOMÁTICO ---
DEFAULT_FILE = "database.xlsx"


@st.cache_data  # Isso faz com que o arquivo não precise ser relido toda hora
def load_data(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df.rename(columns={'P1: State Legitimacy': 'P1: Stats Legitimacy'}, inplace=True)
    df = df.dropna(subset=['Country', 'Year'])
    # Tratamento do Ano
    df['Year'] = pd.to_numeric(df['Year'].astype(str).str.extract('(\d+)', expand=False), errors='coerce')
    df = df.dropna(subset=['Year'])
    df['Year'] = df['Year'].astype(int)
    return df


# Verifica se existe o arquivo padrão ou se o usuário subiu um novo
uploaded_file = st.sidebar.file_uploader("Atualizar Base de Dados (Opcional)", type=["xlsx"])

df = None

if uploaded_file:
    df = load_data(uploaded_file)
    st.sidebar.success("Base de dados atualizada via Upload.")
elif os.path.exists(DEFAULT_FILE):
    df = load_data(DEFAULT_FILE)
    st.sidebar.success("Base de dados institucional carregada.")
else:
    st.info("Aguardando upload de base de dados ou presença do arquivo 'database.xlsx' no servidor.")

if df is not None:
    # --- BARRA LATERAL: PARÂMETROS ---
    st.sidebar.header("⚙️ Configurações Gerais")

    unique_years = sorted(df["Year"].unique(), reverse=True)
    unique_countries = sorted(df["Country"].unique())

    if len(unique_years) > 1:
        selected_year = st.sidebar.select_slider("Ano de Referência:", options=unique_years)
    else:
        selected_year = unique_years[0]

    # Lista de Indicadores Técnicos
    sub_indicators = [
        "S1: Demographic Pressures", "S2: Refugees and IDPs", "C3: Group Grievance",
        "E3: Human Flight and Brain Drain", "E2: Economic Inequality", "E1: Economy",
        "P1: Stats Legitimacy", "P2: Public Services", "P3: Human Rights",
        "C1: Security Apparatus", "C2: Factionalized Elites", "X1: External Intervention"
    ]
    available_sub = [i for i in sub_indicators if i in df.columns]

    # --- NAVEGAÇÃO POR ABAS ---
    tabs = st.tabs(["👤 Perfil por País"] + ["📊 Comparativo Global: " + i for i in (["Total"] + available_sub)])

    # --- ABA 0: PERFIL TRANSVERSAL POR PAÍS ---
    with tabs[0]:
        st.header(f"Análise Multidimensional: {selected_year}")
        col_p1, col_p2 = st.columns([1, 3])

        with col_p1:
            p_country = st.selectbox("Selecione o País:", unique_countries)
            country_data = df[(df["Country"] == p_country) & (df["Year"] == selected_year)]

            if not country_data.empty:
                st.metric("Pontuação Total", f"{country_data['Total'].values[0]:.1f}")
                rank_display = str(country_data['Rank'].values[0]).split('.')[0]
                st.metric("Rank Global", f"Nº {rank_display}")

        with col_p2:
            if not country_data.empty and available_sub:
                df_profile = country_data[available_sub].melt(var_name="Indicador", value_name="Score")
                fig_profile = px.bar(
                    df_profile, x="Score", y="Indicador", orientation='h',
                    title=f"Distribuição de Risco - {p_country}",
                    color="Score", color_continuous_scale=["#2cba00", "#ffa500", "#ff0000"],
                    range_color=[0, 10], text_auto='.2f'
                )
                fig_profile.update_layout(xaxis=dict(range=[0, 10]), height=500, plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_profile, use_container_width=True)

    # --- DEMAIS ABAS: COMPARATIVO GLOBAL ---
    all_indicators = (["Total"] + available_sub)
    for i, sector in enumerate(all_indicators):
        with tabs[i + 1]:
            st.header(f"Benchmarking Global: {sector} ({selected_year})")
            df_year = df[df["Year"] == selected_year]
            avg_value = df_year[sector].mean()

            m1, m2, m3 = st.columns(3)
            m1.metric("Média Global", f"{avg_value:.2f}")
            m2.metric("Pico de Risco", f"{df_year[sector].max():.2f}")
            m3.metric("Maior Estabilidade", f"{df_year[sector].min():.2f}")

            view_mode = st.radio("Filtro:", ["Panorama Geral", "Top 10 - Maior Risco", "Top 10 - Maior Estabilidade"],
                                 key=f"v_{sector}", horizontal=True)

            if view_mode == "Top 10 - Maior Risco":
                df_plot = df_year.nlargest(10, sector).sort_values(sector, ascending=True)
            elif view_mode == "Top 10 - Maior Estabilidade":
                df_plot = df_year.nsmallest(10, sector).sort_values(sector, ascending=False)
            else:
                df_plot = df_year.sort_values(sector, ascending=True)

            fig_bar = px.bar(
                df_plot, x=sector, y="Country", orientation='h',
                color=sector, color_continuous_scale=["#2cba00", "#ffa500", "#ff0000"],
                range_color=[0, 10] if sector != "Total" else [0, 120],
                text_auto='.2f'
            )
            fig_bar.add_vline(x=avg_value, line_dash="dash", line_color="black")
            fig_bar.update_layout(height=max(400, len(df_plot) * 25), plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)