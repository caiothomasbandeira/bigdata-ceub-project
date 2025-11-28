# Big Data Project - CEUB

Projeto de Big Data com Apache Spark e MinIO para análise de dados em larga escala. Este projeto fornece um ambiente completo para processamento distribuído de dados usando Spark e armazenamento em Data Lake com MinIO.

## Visão Geral

Este projeto consiste em dois containers Docker:

1. **MinIO**: Servidor de armazenamento de objetos compatível com S3 (Data Lake)
2. **Spark + Jupyter**: Ambiente de processamento distribuído com interface Jupyter Notebook

Ambos os containers estão conectados através de uma network Docker compartilhada, permitindo comunicação direta entre Spark e MinIO.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                     │
│                    (mybridge)                       │
│                                                     │
│  ┌──────────────────┐      ┌──────────────────┐     │
│  │      MinIO       │      │  Spark + Jupyter │     │
│  │   (Data Lake)    │◄────►│   (Processing)   │     │
│  │                  │      │                  │     │
│  │  Port: 9000      │      │  Port: 8889      │     │
│  │  Port: 9001      │      │  Port: 4040      │     │
│  └──────────────────┘      └──────────────────┘     │
│         │                           │               │
└─────────┼───────────────────────────┼───────────────┘
          │                           │
          ▼                           ▼
    localhost:9001              localhost:8889
   (MinIO Console)           (Jupyter Notebook)
```

## Requisitos

- Docker Desktop (versão 20.10 ou superior)
- Docker Compose v2+
- 4GB RAM mínimo (8GB recomendado)
- 10GB de espaço em disco

### Para Windows

- WSL 2 (recomendado)
- Docker Desktop com WSL Integration habilitado

### Para Linux/MacOS

- Docker e Docker Compose instalados

## Quick Start

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd bigdata-ceub-project
```

### 2. Inicie o MinIO

```bash
cd minio
docker compose up -d
```

Aguarde o container iniciar completamente.

### 3. Inicie o Spark

```bash
cd ../spark
docker compose build  # Primeira vez apenas (demora ~10 minutos)
docker compose up -d
```

### 4. Acesse as Interfaces

**MinIO Console:**
- URL: http://localhost:9001
- User: `minioadmin`
- Password: `minioadmin`

**Jupyter Notebook:**
- URL: http://localhost:8889
- Token: Obtenha com `docker logs spark-jupyter`

### 5. Crie um Bucket no MinIO

1. Acesse http://localhost:9001
2. Login com `minioadmin` / `minioadmin`
3. Crie um bucket chamado `dados`

### 6. Teste o Ambiente

Abra o notebook de exemplo em:
```
http://localhost:8889/lab
```

Navegue até: `exemplo_minio_spark.ipynb`

## Estrutura do Projeto

```
bigdata-ceub-project/
├── README.md                    # Este arquivo
├── minio/                       # Container MinIO
│   ├── docker-compose.yml
│   ├── README.md               # Documentação detalhada do MinIO
│   ├── minio-data/             # Dados persistentes
│   └── minio-backup/           # Backups
├── spark/                       # Container Spark
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── README.md               # Documentação detalhada do Spark
│   ├── notebooks/              # Notebooks Jupyter
│   ├── data/                   # Dados locais
│   └── config/                 # Configurações Jupyter
└──
```

## Containers

### MinIO (Data Lake)

**Portas:**
- 9000: API S3
- 9001: Console Web

**Volumes:**
- `./minio/minio-data`: Dados do MinIO
- `./minio/minio-backup`: Backups

**Documentação completa:** [minio/README.md](minio/README.md)

### Spark + Jupyter

**Portas:**
- 8889: Jupyter Notebook
- 4040: Spark UI
- 7077: Spark Master

**Volumes:**
- `./spark/notebooks`: Notebooks Jupyter
- `./spark/data`: Dados locais
- `./spark/config`: Configurações

**Tecnologias:**
- Apache Spark 3.5.7
- Python 3.x
- PySpark, Pandas, Matplotlib, Seaborn
- Delta Lake 3.2.1
- Hadoop-AWS (S3 connector)

**Documentação completa:** [spark/README.md](spark/README.md)

## Comandos Úteis

### Gerenciamento de Containers

```bash
# Iniciar todos os containers
docker compose -f minio/docker-compose.yml up -d
docker compose -f spark/docker-compose.yml up -d

# Parar todos os containers
docker compose -f spark/docker-compose.yml down
docker compose -f minio/docker-compose.yml down

# Ver status
docker ps

# Ver logs
docker logs minio
docker logs spark-jupyter

# Logs em tempo real
docker logs -f spark-jupyter
```

### Verificações

```bash
# Verificar network
docker network ls | grep mybridge
docker network inspect mybridge

# Verificar containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Testar conectividade Spark -> MinIO
docker exec spark-jupyter ping minio
```

### Manutenção

```bash
# Rebuild do Spark (após mudanças no Dockerfile)
cd spark
docker compose build --no-cache
docker compose up -d

# Restart dos containers
docker restart minio
docker restart spark-jupyter

# Ver uso de recursos
docker stats
```

### Limpeza

```bash
# Parar e remover containers
docker compose -f spark/docker-compose.yml down
docker compose -f minio/docker-compose.yml down

# Remover volumes (CUIDADO: apaga dados)
docker volume prune

# Remover imagens não usadas
docker image prune -a
```

## Acesso Rápido

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| MinIO API | http://localhost:9000 | - |
| Jupyter Notebook | http://localhost:8889 | Token nos logs |
| Spark UI | http://localhost:4040 | - |

## Workflow Típico

### 1. Preparar Dados

```bash
# Upload via MinIO Console
http://localhost:9001

# Ou via MinIO Client (mc)
mc cp dados.csv myminio/dados/
```

### 2. Processar com Spark

```python
# No Jupyter Notebook
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

df = spark.read.csv("s3a://dados/dados.csv", header=True, inferSchema=True)
df.show()
```

### 3. Analisar

```python
# Análise exploratória
df.describe().show()
df.groupBy("coluna").count().show()

# Conversão para Pandas
pdf = df.toPandas()

# Visualização
import matplotlib.pyplot as plt
pdf['coluna'].plot(kind='hist')
plt.show()
```

### 4. Salvar Resultados

```python
# Salvar processado no MinIO
df.write.mode("overwrite").parquet("s3a://dados/processado/")

# Ou Delta Lake
df.write.format("delta").mode("overwrite").save("s3a://dados/delta/")
```

## Formatos Suportados

### Leitura e Escrita

- **CSV**: Dados tabulares com separadores
- **Parquet**: Formato colunar otimizado
- **JSON**: Dados semi-estruturados
- **Delta Lake**: Formato transacional com versionamento
- **Avro**: Serialização binária (adicionar JAR se necessário)

### Exemplo de Leitura

```python
# CSV
df = spark.read.option("header", "true").csv("s3a://dados/arquivo.csv")

# Parquet
df = spark.read.parquet("s3a://dados/arquivo.parquet")

# JSON
df = spark.read.json("s3a://dados/arquivo.json")

# Delta
df = spark.read.format("delta").load("s3a://dados/tabela/")
```

## Performance

### Otimizações Recomendadas

1. **Particionamento**: Divida dados por data ou categoria
   ```python
   df.write.partitionBy("ano", "mes").parquet("s3a://dados/particionado/")
   ```

2. **Cache**: Mantenha DataFrames em memória
   ```python
   df.cache()
   ```

3. **Reparticionamento**: Ajuste número de partições
   ```python
   df.repartition(10).write.parquet("s3a://dados/saida/")
   ```

4. **Formato Parquet**: Use para melhor compressão e velocidade

## Segurança

### Desenvolvimento (Padrão Atual)

- Credenciais: `minioadmin` / `minioadmin`
- Sem autenticação adicional
- Network interna Docker

### Produção (Recomendações)

1. **Alterar credenciais MinIO**:
   ```yaml
   environment:
     MINIO_ROOT_USER: usuario_seguro
     MINIO_ROOT_PASSWORD: senha_forte_complexa
   ```

2. **Configurar HTTPS**:
   - Use certificados TLS
   - Configure reverse proxy

3. **Políticas de acesso**:
   - Crie usuários específicos no MinIO
   - Defina permissões IAM granulares

4. **Network isolada**:
   - Use networks Docker isoladas
   - Configure firewall

5. **Jupyter com senha**:
   - Configure senha permanente no primeiro acesso

## Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker logs <container-name> --tail 100

# Verificar portas em uso
netstat -ano | findstr :9000
netstat -ano | findstr :8889

# Verificar Docker
docker version
docker compose version
```

### Erro de network

```bash
# Verificar se network existe
docker network ls | grep mybridge

# Recriar network manualmente
docker network create mybridge

# Verificar conexão entre containers
docker network inspect mybridge
```

### Build muito lento

O primeiro build do Spark demora ~10 minutos:
- Download do Spark: ~400MB
- Download de JARs: ~100MB
- Instalação de pacotes Python

Builds subsequentes usam cache e são mais rápidos.

### Erro ao acessar MinIO do Spark

1. Verifique se MinIO está rodando: `docker ps`
2. Teste conectividade: `docker exec spark-jupyter ping minio`
3. Verifique se estão na mesma network: `docker network inspect mybridge`
4. Verifique endpoint na configuração Spark: deve ser `http://minio:9000`

### Jupyter sem token

```bash
# Extrair token dos logs
docker logs spark-jupyter 2>&1 | grep token

# Ou gerar novo token
docker exec spark-jupyter jupyter notebook list
```

## Recursos de Aprendizado

### Documentação Oficial

- [Apache Spark](https://spark.apache.org/docs/latest/)
- [PySpark API](https://spark.apache.org/docs/latest/api/python/)
- [MinIO](https://min.io/docs/minio/linux/index.html)
- [Delta Lake](https://docs.delta.io/latest/index.html)
- [JupyterLab](https://jupyterlab.readthedocs.io/)

### Tutoriais

- [PySpark Tutorial](https://sparkbyexamples.com/pyspark-tutorial/)
- [Delta Lake Quickstart](https://docs.delta.io/latest/quick-start.html)
- [S3A Hadoop](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/index.html)

## Suporte

Para documentação detalhada de cada componente:

- **MinIO**: Consulte [minio/README.md](minio/README.md)
- **Spark**: Consulte [spark/README.md](spark/README.md)

## Contribuindo

Para contribuir com este projeto:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## Licença

- Este projeto é para fins educacionais - CEUB (Centro Universitário de Brasília).
- Projeto desenvolvido para disciplina de Fundamentos de Big Data do 4º semestre com professor Klayton Rodrigues de Castro

## Autores

|        Nome Completo       |    RA    |
|----------------------------|----------|
| Caio Thomas Silva Bandeira | 22407182 |
| Luis Vinicius Hernani      | 22402740 |
| Arthur Gonçalves Farias dos Reis | 22409753 |
| Vinícius César Sena Torres | 22409225 |

---

Sempre inicie o MinIO antes do Spark, pois o Spark depende da network criada pelo MinIO.
