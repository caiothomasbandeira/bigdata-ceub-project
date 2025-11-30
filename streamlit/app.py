from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Trase Brazil Beef Dashboard", layout="wide")

st.title("📊 Trase Brazil Beef Dashboard")
st.caption(
    "Interface Streamlit para explorar rapidamente os dados utilizados nas análises do projeto. "
    "Você pode ler o CSV diretamente do MinIO ou carregar um arquivo local montado no container."
)

DATA_DIR = Path(os.environ.get("TRASE_DATA_DIR", "/app/data"))
DEFAULT_FILE = DATA_DIR / "trase_data" / "brazil_beef_v2_2_1" / "brazil_beef_v2_2_1.csv"

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "dados")
MINIO_OBJECT = os.environ.get(
    "MINIO_OBJECT", "trase/brazil_beef/raw/full_csv_dump/part-00000-114a77a7-d9d3-41e0-87d6-e030ade2cb52-c000.snappy.parquet.docker ps"
)


@st.cache_data(show_spinner=False)
def load_local_csv(path: Path):
    return pd.read_csv(path)


@st.cache_data(show_spinner=True)
def load_minio_csv(bucket: str, key: str):
    url = f"s3://{bucket}/{key}"
    storage_options = {
        "key": MINIO_ACCESS_KEY,
        "secret": MINIO_SECRET_KEY,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT},
    }
    return pd.read_csv(url, storage_options=storage_options)


st.sidebar.header("Configurações de Dados")
data_source = st.sidebar.radio("Fonte dos dados", ("MinIO", "Arquivo local"))

df = None

if data_source == "MinIO":
    st.sidebar.markdown("### MinIO")
    bucket_name = st.sidebar.text_input("Bucket", value=MINIO_BUCKET)
    object_path = st.sidebar.text_input("Objeto CSV", value=MINIO_OBJECT)
    if st.sidebar.button("Carregar do MinIO"):
        try:
            df = load_minio_csv(bucket_name, object_path)
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
            "Arquivo não encontrado. Verifique se o volume compartilhado está configurado em `docker-compose.yml`.\n"
            "Dica: o compose monta `../spark/data` como `/app/data`. Rode o notebook de ingestão ou copie o CSV para lá."
        )

if df is None:
    st.stop()

st.subheader("Visão Geral do Dataset")
st.write("Linhas", len(df))
st.write("Colunas", list(df.columns))

st.subheader("Prévia")
st.dataframe(df.head(50))

st.subheader("Visualização rápida")
numeric_cols = df.select_dtypes(include="number").columns.tolist()
if numeric_cols:
    y_axis = st.selectbox("Coluna numérica para histograma", numeric_cols)
    fig = px.histogram(df, x=y_axis, nbins=40, title=f"Distribuição de {y_axis}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma coluna numérica disponível para plotar.")
