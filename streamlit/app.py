from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================
# Config básica
# =========================
st.set_page_config(page_title="Trase Brazil Beef Dashboard", layout="wide")

st.title("Trase Brazil Beef Dashboard")
st.caption(
    "Interface Streamlit para explorar rapidamente os dados utilizados nas análises do projeto. "
    "Você pode ler o CSV diretamente do MinIO ou carregar um arquivo local montado no container."
)

DATA_DIR = Path(os.environ.get("TRASE_DATA_DIR", "/app/data"))
DEFAULT_FILE = DATA_DIR / "trase_data" / "brazil_beef_v2_2_1" / "brazil_beef_v2_2_1.csv"

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "dados-supplychain")
MINIO_OBJECT = os.environ.get("MINIO_OBJECT", "trase/brazil_beef/raw/full_csv_dump/")

# =========================
# Leitura de dados
# =========================
@st.cache_data(show_spinner=False)
def load_local_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=True)
def load_minio_parquet(bucket: str, key: str) -> pd.DataFrame:
    url = f"s3://{bucket}/{key}"
    storage_options = {
        "key": MINIO_ACCESS_KEY,
        "secret": MINIO_SECRET_KEY,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT},
    }
    return pd.read_parquet(url, storage_options=storage_options)


st.sidebar.header("Configurações de Dados")
data_source = st.sidebar.radio("Fonte dos dados", ("MinIO", "Arquivo local"))

df = None

if data_source == "MinIO":
    st.sidebar.markdown("### MinIO")
    bucket_name = st.sidebar.text_input("Bucket", value=MINIO_BUCKET)
    object_path = st.sidebar.text_input("Caminho Parquet", value=MINIO_OBJECT)

    if st.sidebar.button("Carregar do MinIO"):
        try:
            df = load_minio_parquet(bucket_name, object_path)
            st.success(f"Arquivo carregado do MinIO: s3://{bucket_name}/{object_path}")
        except Exception as exc:
            st.error(f"Erro ao ler do MinIO: {exc}")
else:
    st.sidebar.markdown("### Arquivo local")
    custom_path = st.sidebar.text_input(
        "Caminho local dentro do container", value=str(DEFAULT_FILE)
    )
    csv_path = Path(custom_path)
    if csv_path.exists():
        try:
            df = load_local_csv(csv_path)
            st.success(f"Arquivo local carregado: {csv_path}")
        except Exception as exc:
            st.error(f"Erro ao ler o arquivo local: {exc}")
    else:
        st.warning(
            "Arquivo não encontrado. Verifique se o volume compartilhado está configurado em docker-compose.yml.\n"
            "Dica: o compose monta ../spark/data como /app/data. Rode o notebook de ingestão ou copie o CSV para lá."
        )

if df is None:
    st.stop()

# =========================
# Visão geral rápida
# =========================
st.subheader("Visão Geral do Dataset")
col_a, col_b = st.columns(2)
with col_a:
    st.write("*Linhas*", len(df))
with col_b:
    st.write("*Colunas*", len(df.columns))

with st.expander("Ver nomes das colunas"):
    st.write(list(df.columns))

# =========================
# Descobrir colunas úteis (sem alterar o df)
# =========================
numeric_cols = df.select_dtypes(include="number").columns.tolist()

# Colunas típicas do Trase (usadas só se realmente existirem)
POTENTIAL_YEAR_COLS = ["year", "ano"]
YEAR_COL = next((c for c in POTENTIAL_YEAR_COLS if c in df.columns), None)

POTENTIAL_DIMENSION_COLUMNS = [
    "municipality_of_production",
    "state_of_production",
    "biome",
    "exporter_group",
    "exporter",
    "trader",
    "importer",
    "country_of_destination",
    "destination",
]
available_dims = [c for c in POTENTIAL_DIMENSION_COLUMNS if c in df.columns]

# Ordem default inspirada no link do Trase
default_flow_dims = [
    c
    for c in [
        "municipality_of_production",
        "exporter_group",
        "importer",
        "country_of_destination",
    ]
    if c in available_dims
]

# Métricas típicas do Trase + fallback para qualquer numérica
PREFERRED_METRIC_COLS = [
    "total_volume_t",
    "total_fob_usd",
    "cattle_deforestation_5_year_total_exposure",
    "total_co2_gross_tco2",
    "total_co2_net_tco2",
    "total_pasture_area_ha",
]
available_metric_cols = [c for c in PREFERRED_METRIC_COLS if c in df.columns]
if not available_metric_cols:
    available_metric_cols = numeric_cols[:]  # fallback genérico

METRIC_LABELS = {
    "total_volume_t": "Trade volume (t)",
    "total_fob_usd": "Trade value (USD)",
    "cattle_deforestation_5_year_total_exposure": "Cattle deforestation exposure (ha)",
    "total_co2_gross_tco2": "Gross emissions from cattle deforestation (t CO₂-eq.)",
    "total_co2_net_tco2": "Net emissions from cattle deforestation (t CO₂-eq.)",
    "total_pasture_area_ha": "Pasture area (ha)",
}

# =========================
# Filtros – Sidebar (imitando painel do Trase)
# =========================
st.sidebar.markdown("---")
st.sidebar.header("Filtros")

# Ano
if YEAR_COL:
    years_sorted = sorted(df[YEAR_COL].dropna().unique())
    selected_years = st.sidebar.multiselect(
        "Ano(s)",
        options=years_sorted,
        default=[max(years_sorted)] if len(years_sorted) > 0 else years_sorted,
    )
else:
    selected_years = None

# Métrica
metric_col = st.sidebar.selectbox("Métrica", options=available_metric_cols)
metric_label = METRIC_LABELS.get(metric_col, metric_col)

# Mostrar / ocultar consumo doméstico (se houver país de destino)
if "country_of_destination" in df.columns:
    include_domestic = st.sidebar.checkbox(
        "Incluir consumo doméstico (destino = Brasil)", value=False
    )
else:
    include_domestic = True  # não filtra nada se a coluna não existe

st.sidebar.markdown("### Dimensões (Sankey)")
if available_dims:
    flow_dims = st.sidebar.multiselect(
        "Ordem das dimensões",
        options=available_dims,
        default=default_flow_dims or available_dims[:4],
        help="As dimensões serão usadas da esquerda para a direita no diagrama Sankey.",
    )
else:
    flow_dims = []

# Alguns filtros opcionais por dimensão famosa
if "biome" in df.columns:
    biomes = sorted(df["biome"].dropna().unique())
    selected_biomes = st.sidebar.multiselect("Bioma", options=biomes, default=biomes)
else:
    selected_biomes = None

if "state_of_production" in df.columns:
    states = sorted(df["state_of_production"].dropna().unique())
    selected_states = st.sidebar.multiselect(
        "Estado de produção", options=states, default=states
    )
else:
    selected_states = None

if "exporter_group" in df.columns:
    exporters = sorted(df["exporter_group"].dropna().unique())
    selected_exporters = st.sidebar.multiselect(
        "Exportador (grupo)", options=exporters, default=exporters
    )
else:
    selected_exporters = None

if "country_of_destination" in df.columns:
    countries = sorted(df["country_of_destination"].dropna().unique())
    selected_countries = st.sidebar.multiselect(
        "País de destino", options=countries, default=countries
    )
else:
    selected_countries = None


# =========================
# Aplicar filtros no DataFrame
# =========================
def apply_filters(df_in: pd.DataFrame) -> pd.DataFrame:
    df_f = df_in

    if YEAR_COL and selected_years:
        df_f = df_f[df_f[YEAR_COL].isin(selected_years)]

    if selected_biomes is not None:
        df_f = df_f[df_f["biome"].isin(selected_biomes)]

    if selected_states is not None:
        df_f = df_f[df_f["state_of_production"].isin(selected_states)]

    if selected_exporters is not None:
        df_f = df_f[df_f["exporter_group"].isin(selected_exporters)]

    if selected_countries is not None:
        df_f = df_f[df_f["country_of_destination"].isin(selected_countries)]

    if "country_of_destination" in df_f.columns and not include_domestic:
        df_f = df_f[df_f["country_of_destination"] != "Brazil"]

    return df_f


df_filtered = apply_filters(df)

# =========================
# Abas principais (imitando Trase)
# =========================
tab_flows, tab_ranking, tab_time, tab_keys, tab_table = st.tabs(
    ["Flows (Sankey)", "Ranking", "Over time", "Key numbers", "Tabela"]
)

# ---------- ABA: FLOWS (SANKEY) ----------
with tab_flows:
    st.subheader("Fluxos da cadeia de suprimentos")

    if not flow_dims or len(flow_dims) < 2:
        st.info(
            "Selecione pelo menos *duas dimensões* na barra lateral para montar o diagrama Sankey."
        )
    elif metric_col not in df_filtered.columns:
        st.error(f"A métrica selecionada {metric_col} não existe no DataFrame.")
    else:
        # Agrupar pelos nós selecionados
        group_cols = flow_dims
        df_grouped = (
            df_filtered[group_cols + [metric_col]]
            .dropna(subset=group_cols)
            .groupby(group_cols, as_index=False)[metric_col]
            .sum()
        )

        # Para evitar explodir o navegador, limitar ao top N fluxos
        top_n_flows = st.slider(
            "Quantidade máxima de fluxos (linhas agrupadas)",
            min_value=50,
            max_value=1000,
            value=300,
            step=50,
        )
        df_grouped = df_grouped.sort_values(metric_col, ascending=False).head(
            top_n_flows
        )

        # Criar índice de nós únicos
        all_labels = []
        for col in group_cols:
            all_labels.extend(df_grouped[col].astype(str).unique().tolist())
        labels = sorted(set(all_labels))
        label_to_id = {label: i for i, label in enumerate(labels)}

        # Construir listas source/target/value
        sources = []
        targets = []
        values = []

        for _, row in df_grouped.iterrows():
            for i in range(len(group_cols) - 1):
                src_label = str(row[group_cols[i]])
                tgt_label = str(row[group_cols[i + 1]])
                sources.append(label_to_id[src_label])
                targets.append(label_to_id[tgt_label])
                values.append(row[metric_col])

        if not values:
            st.warning("Nenhum fluxo disponível após aplicar os filtros.")
        else:
            sankey_fig = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=15,
                            thickness=15,
                            line=dict(width=0.5),
                            label=labels,
                        ),
                        link=dict(source=sources, target=targets, value=values),
                    )
                ]
            )
            sankey_fig.update_layout(
                title_text=f"Fluxos por {' → '.join(flow_dims)} — {metric_label}",
                font=dict(size=10),
            )
            st.plotly_chart(sankey_fig, use_container_width=True)

# ---------- ABA: RANKING ----------
with tab_ranking:
    st.subheader("Ranking")

    # Selecionar dimensão para ranking
    rank_dims_candidates = available_dims or [
        c for c in df_filtered.columns if c not in numeric_cols
    ]
    if not rank_dims_candidates:
        st.info("Não há colunas categóricas suficientes para montar rankings.")
    elif metric_col not in df_filtered.columns:
        st.error(f"A métrica selecionada {metric_col} não existe no DataFrame.")
    else:
        ranking_dim = st.selectbox("Dimensão para ranking", options=rank_dims_candidates)

        top_n = st.slider("Top N", min_value=5, max_value=100, value=20, step=5)

        df_rank = (
            df_filtered[[ranking_dim, metric_col]]
            .dropna(subset=[ranking_dim])
            .groupby(ranking_dim, as_index=False)[metric_col]
            .sum()
        )
        df_rank = df_rank.sort_values(metric_col, ascending=False).head(top_n)

        fig_rank = px.bar(
            df_rank,
            x=metric_col,
            y=ranking_dim,
            orientation="h",
            title=f"Top {top_n} por {ranking_dim} — {metric_label}",
        )
        fig_rank.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_rank, use_container_width=True)

        with st.expander("Ver dados do ranking"):
            st.dataframe(df_rank)

# ---------- ABA: OVER TIME ----------
with tab_time:
    st.subheader("Evolução temporal")

    if YEAR_COL is None:
        st.info("Não foi encontrada uma coluna de ano (ex.: 'year').")
    elif metric_col not in df_filtered.columns:
        st.error(f"A métrica selecionada {metric_col} não existe no DataFrame.")
    else:
        # Permitir quebrar a série por uma dimensão opcional
        time_group_dim = None
        candidates = [c for c in available_dims if c != YEAR_COL]
        if candidates:
            time_group_dim = st.selectbox(
                "Quebrar por (opcional)", options=["(sem agrupamento)"] + candidates
            )
            if time_group_dim == "(sem agrupamento)":
                time_group_dim = None

        group_cols = [YEAR_COL] + ([time_group_dim] if time_group_dim else [])
        df_time = (
            df_filtered[group_cols + [metric_col]]
            .dropna(subset=[YEAR_COL])
            .groupby(group_cols, as_index=False)[metric_col]
            .sum()
        )

        if time_group_dim:
            fig_time = px.line(
                df_time,
                x=YEAR_COL,
                y=metric_col,
                color=time_group_dim,
                markers=True,
                title=f"{metric_label} ao longo do tempo por {time_group_dim}",
            )
        else:
            fig_time = px.line(
                df_time,
                x=YEAR_COL,
                y=metric_col,
                markers=True,
                title=f"{metric_label} ao longo do tempo",
            )

        st.plotly_chart(fig_time, use_container_width=True)

        with st.expander("Ver dados da série temporal"):
            st.dataframe(df_time)

# ---------- ABA: KEY NUMBERS ----------
with tab_keys:
    st.subheader("Números-chave (Key numbers)")

    # KPI principal: total da métrica nos filtros
    total_metric = df_filtered[metric_col].sum() if metric_col in df_filtered.columns else None

    col1, col2, col3 = st.columns(3)

    if total_metric is not None:
        with col1:
            st.metric(
                label=f"Total — {metric_label}",
                value=f"{total_metric:,.0f}".replace(",", "."),
            )

    # Número de municípios / estados / países distintos, se existirem
    if "municipality_of_production" in df_filtered.columns:
        with col2:
            n_mun = df_filtered["municipality_of_production"].nunique()
            st.metric("Municípios de produção", f"{n_mun:,}".replace(",", "."))

    if "country_of_destination" in df_filtered.columns:
        with col3:
            n_dest = df_filtered["country_of_destination"].nunique()
            st.metric("Países de destino", f"{n_dest:,}".replace(",", "."))

    # Tabela resumida por estado e bioma (se existirem)
    if (
        "state_of_production" in df_filtered.columns
        and "biome" in df_filtered.columns
        and metric_col in df_filtered.columns
    ):
        st.markdown("### Resumo por estado e bioma")
        df_state_biome = (
            df_filtered[["state_of_production", "biome", metric_col]]
            .groupby(["state_of_production", "biome"], as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )
        st.dataframe(df_state_biome)

# ---------- ABA: TABELA ----------
with tab_table:
    st.subheader("Tabela de dados filtrados")

    st.write(
        "Abaixo, os dados *apenas com filtros aplicados*, sem agregações adicionais "
        "(exceto as usadas nos gráficos nas outras abas)."
    )

    st.dataframe(df_filtered)

    st.markdown("### Amostra rápida (head)")
    st.dataframe(df_filtered.head(50))