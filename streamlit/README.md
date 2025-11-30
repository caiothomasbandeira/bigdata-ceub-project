# Streamlit Dashboard

Serviço Streamlit dockerizado para visualizar rapidamente os dados do projeto. O container utiliza a mesma rede externa `mybridge` para conversar com os demais serviços (MinIO/Spark), consegue buscar arquivos diretamente do bucket `dados` via API S3 e também monta `../spark/data` em modo somente leitura, permitindo reaproveitar os arquivos locais gerados pelos notebooks.

## Pré-requisitos

- Docker / Docker Compose v2+
- Rede Docker `mybridge` já criada (`docker network create mybridge`)
- Opcional: dados disponíveis em `spark/data/trase_data/brazil_beef_v2_2_1/brazil_beef_v2_2_1.csv` (os notebooks de ingestão baixam esse arquivo automaticamente) caso queira usar a fonte “Arquivo local”

## Como executar

```bash
cd streamlit
docker compose up --build
```

A interface ficará disponível em http://localhost:8501.

Para editar a interface, modifique `app.py`. O arquivo é montado como volume dentro do container, permitindo hot reload.

No painel lateral você escolhe entre:
- **MinIO**: lê diretamente do bucket usando as variáveis `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` e `MINIO_OBJECT` (já definidas no `docker-compose.yml`). Ajuste-as conforme necessário ou digite outro bucket/objeto no formulário.
- **Arquivo local**: mantém o comportamento anterior, lendo o CSV montado em `/app/data`. Nesse caso vale ajustar `TRASE_DATA_DIR` ou simplesmente copiar o arquivo para `../spark/data`.
