from pathlib import Path
import os
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import pyarrow.dataset as ds
import s3fs
import streamlit as st

st.set_page_config(page_title="Trase Brazil Beef Dashboard", layout="wide")

st.title("Trase Brazil Beef Dashboard")
st.caption(
    "Interface Streamlit para explorar rapidamente os dados utilizados nas analises do projeto. "
    "Voce pode ler arquivos diretamente do MinIO ou carregar um arquivo local montado no container."
)

DATA_DIR = Path(os.environ.get("TRASE_DATA_DIR", "/app/data"))
DEFAULT_FILE = DATA_DIR / "trase_data" / "brazil_beef_v2_2_1" / "brazil_beef_v2_2_1.csv"
DATA_PREVIEW_LIMIT = int(os.environ.get("STREAMLIT_MAX_ROWS", "200000"))

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "dados-supplychain")
MINIO_OBJECT = os.environ.get(
    "MINIO_OBJECT", "trase/brazil_beef/raw/full_csv_dump/"
)


def _create_s3_fs(storage_options):
    if not storage_options:
        return None
    storage_options = dict(storage_options)
    client_kwargs = storage_options.get("client_kwargs", {})
    return s3fs.S3FileSystem(
        key=storage_options.get("key"),
        secret=storage_options.get("secret"),
        client_kwargs=client_kwargs,
    )


def _dataset_from_path(path: str, storage_options=None):
    if path.startswith("s3://"):
        parsed = urlparse(path)
        dataset_path = f"{parsed.netloc}{parsed.path}".rstrip("/")
        fs = _create_s3_fs(storage_options)
        return ds.dataset(dataset_path, filesystem=fs, format="parquet")
    return ds.dataset(path, format="parquet")


def _read_dataframe(path: str, storage_options=None):
    if path.endswith(".parquet") or path.endswith("/"):
        dataset = _dataset_from_path(path, storage_options)
        table = dataset.to_table(limit=DATA_PREVIEW_LIMIT)
        pdf = table.to_pandas()
        return pdf, len(pdf) == DATA_PREVIEW_LIMIT
    df = pd.read_csv(path, storage_options=storage_options)
    return df, False


@st.cache_data(show_spinner=False)
def load_local_data(path: Path):
    target = str(path)
    if path.is_dir() and not target.endswith("/"):
        target += "/"
    return _read_dataframe(target)


@st.cache_data(show_spinner=True)
def load_minio_data(bucket: str, key: str):
    url = f"s3://{bucket}/{key}"
    storage_options = {
        "key": MINIO_ACCESS_KEY,
        "secret": MINIO_SECRET_KEY,
        "client_kwargs": {"endpoint_url": MINIO_ENDPOINT},
    }
    return _read_dataframe(url, storage_options=storage_options)


st.sidebar.header("Configuracoes de Dados")
data_source = st.sidebar.radio("Fonte dos dados", ("MinIO", "Arquivo local"))

result = None
if data_source == "MinIO":
    st.sidebar.markdown("### MinIO")
    bucket_name = st.sidebar.text_input("Bucket", value=MINIO_BUCKET)
    object_path = st.sidebar.text_input("Objeto (CSV ou Parquet)", value=MINIO_OBJECT)
    if st.sidebar.button("Carregar do MinIO"):
        try:
            result = load_minio_data(bucket_name, object_path)
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
            result = load_local_data(csv_path)
            st.success(f"Arquivo local carregado: {csv_path}")
        except Exception as exc:
            st.error(f"Erro ao ler o arquivo local: {exc}")
    else:
        st.warning(
            "Arquivo nao encontrado. Verifique se o volume compartilhado esta configurado em docker-compose.yml.\n"
            "Dica: o compose monta ../spark/data como /app/data. Rode o notebook de ingestao ou copie o arquivo para la."
        )

if result is None:
    st.stop()

df, truncated = result

st.subheader("Visao Geral do Dataset")
st.write("Linhas carregadas", len(df))
st.write("Colunas", list(df.columns))
if truncated:
    st.info(f"Exibindo no maximo {DATA_PREVIEW_LIMIT:,} linhas para evitar alto consumo de memoria.")

st.subheader("Previa")
st.dataframe(df.head(50))

st.subheader("Visualizacao rapida")
numeric_cols = df.select_dtypes(include="number").columns.tolist()
if numeric_cols:
    y_axis = st.selectbox("Coluna numerica para histograma", numeric_cols)
    fig = px.histogram(df, x=y_axis, nbins=40, title=f"Distribuicao de {y_axis}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma coluna numerica disponivel para plotar.")
