# Spark + Jupyter Notebook

Container customizado com Apache Spark e Jupyter Notebook para análise de Big Data, com suporte completo a MinIO (S3) e Delta Lake.

## Configuração

### Estrutura de Diretórios

```
spark/
├── docker-compose.yml       # Configuração do container
├── Dockerfile              # Build da imagem customizada
├── notebooks/              # Notebooks Jupyter
├── data/                   # Dados locais
└── config/                 # Configurações do Jupyter
```

### Especificações do Container

- **Base Image:** `jupyter/base-notebook:latest`
- **Container Name:** `spark-jupyter`
- **Network:** `mybridge` (compartilhada com MinIO)
- **Java Version:** OpenJDK 11
- **Spark Version:** 3.5.7
- **Python Version:** 3.x (da imagem base)

### Portas Expostas

- **8888:** Jupyter Notebook (mapeada para 8889 no host)
- **4040:** Spark UI (interface de monitoramento)
- **7077:** Spark Master (comunicação interna)

### Bibliotecas Python Instaladas

- **pyspark 3.5.7** - Interface Python para Spark
- **pandas** - Manipulação de dados
- **matplotlib** - Visualização
- **seaborn** - Visualização estatística
- **boto3** - AWS SDK (para S3/MinIO)
- **delta-spark 3.2.1** - Suporte a Delta Lake

### JARs Incluídos

- **hadoop-aws 3.3.2** - Conectividade S3/MinIO
- **aws-java-sdk-bundle 1.11.1026** - SDK AWS
- **delta-spark 3.2.1** - Delta Lake Core
- **delta-storage 3.2.1** - Delta Lake Storage

### Ferramentas Adicionais

- **MinIO Client (mc)** - CLI para gerenciar MinIO
- **sudo** - Permissões administrativas no container

## Como Rodar

### Build da Imagem

```bash
# No diretório spark/
docker compose build
```

O build demora aproximadamente 10 minutos na primeira vez (baixa Spark, JARs, etc).

### Iniciar o Container

```bash
# Certifique-se que MinIO está rodando primeiro
cd ../minio
docker compose up -d

# Depois inicie o Spark
cd ../spark
docker compose up -d
```

### Verificar Status

```bash
# Ver logs
docker logs spark-jupyter

# Ver logs em tempo real
docker logs -f spark-jupyter

# Ver status do container
docker ps | grep spark-jupyter
```

### Parar o Container

```bash
# Parar e remover container
docker compose down

# Parar sem remover
docker compose stop
```

### Reiniciar o Container

```bash
docker compose restart
```

## Acessar Jupyter Notebook

### Obter Token de Acesso

```bash
# Ver logs para encontrar o token
docker logs spark-jupyter
```

Procure por uma linha similar a:
```
http://127.0.0.1:8888/lab?token=abc123def456...
```

### Acessar Interface Web

1. **URL:** http://localhost:8889
2. **Token:** Use o token obtido nos logs acima
3. Cole o token no campo de autenticação

### Alternativa: URL Completa

```bash
# Copie a URL dos logs e substitua a porta 8888 por 8889
http://localhost:8889/lab?token=SEU_TOKEN_AQUI
```

### Configurar Senha (Opcional)

1. Acesse com o token
2. No menu: File > Hub Control Panel
3. Configure uma senha permanente

## Interfaces Gráficas

### Jupyter Lab

- **URL:** http://localhost:8889
- **Autenticação:** Token ou senha
- **Funcionalidades:**
  - Editor de notebooks
  - Terminal integrado
  - Explorador de arquivos
  - Visualização de dados
  - Extensões disponíveis

### Spark UI

- **URL:** http://localhost:4040
- **Disponível:** Somente quando Spark está executando jobs
- **Funcionalidades:**
  - Monitorar jobs em execução
  - Ver stages e tasks
  - Analisar DAG de execução
  - Métricas de performance
  - Logs de executors

**Nota:** A Spark UI só fica disponível durante a execução de um SparkSession ativo.

## Criar SparkSession

### Configuração Básica

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MeuApp") \
    .getOrCreate()
```

### Configuração com MinIO

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Spark-MinIO") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .getOrCreate()
```

### Configuração com Delta Lake

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Spark-Delta") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:3.2.1") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()
```

## Usar MinIO (S3)

### Ler Dados

```python
# CSV
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("s3a://dados/arquivo.csv")

# Parquet
df = spark.read.parquet("s3a://dados/arquivo.parquet")

# JSON
df = spark.read.json("s3a://dados/arquivo.json")

# Delta Lake
df = spark.read.format("delta").load("s3a://dados/tabela_delta/")
```

### Escrever Dados

```python
# CSV
df.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv("s3a://dados/saida.csv")

# Parquet
df.write \
    .mode("overwrite") \
    .parquet("s3a://dados/saida.parquet")

# Delta Lake
df.write \
    .format("delta") \
    .mode("overwrite") \
    .save("s3a://dados/tabela_delta/")
```

## Notebooks Incluídos

### exemplo_minio_spark.ipynb

Notebook de exemplo com:
- Conexão Spark + MinIO
- Criação de dados de exemplo
- Leitura e escrita em diferentes formatos (CSV, Parquet, Delta)
- Análises básicas com PySpark
- Visualizações com Matplotlib e Seaborn

**Localização:** `/home/jovyan/work/exemplo_minio_spark.ipynb`

## Variáveis de Ambiente

```yaml
JUPYTER_ENABLE_LAB: yes              # Habilita JupyterLab
GRANT_SUDO: yes                       # Permite uso de sudo
AWS_ACCESS_KEY_ID: minioadmin         # Credencial MinIO
AWS_SECRET_ACCESS_KEY: minioadmin     # Credencial MinIO
AWS_REGION: us-east-1                 # Região AWS (padrão)
```

## Volumes Persistentes

### notebooks/
- **Path no Container:** `/home/jovyan/work`
- **Path no Host:** `./notebooks`
- **Descrição:** Todos os notebooks criados são salvos aqui

### data/
- **Path no Container:** `/home/jovyan/data`
- **Path no Host:** `./data`
- **Descrição:** Dados locais para análise

### config/
- **Path no Container:** `/home/jovyan/.jupyter`
- **Path no Host:** `./config`
- **Descrição:** Configurações do Jupyter (workspace, extensões)

## Comandos Docker Úteis

### Logs e Monitoramento

```bash
# Ver logs completos
docker logs spark-jupyter

# Logs em tempo real
docker logs -f spark-jupyter

# Ver uso de recursos
docker stats spark-jupyter

# Inspecionar container
docker inspect spark-jupyter
```

### Acesso ao Container

```bash
# Shell bash
docker exec -it spark-jupyter bash

# Executar comando específico
docker exec spark-jupyter python --version
docker exec spark-jupyter spark-submit --version
```

### Rebuild

```bash
# Rebuild forçado (sem cache)
docker compose build --no-cache

# Rebuild e restart
docker compose up -d --build
```

## Terminal Integrado

O Jupyter Lab possui terminal integrado:

1. Acesse http://localhost:8889
2. Menu: File > New > Terminal
3. Use comandos diretamente no container

### Comandos Úteis no Terminal

```bash
# Verificar versão do Spark
spark-submit --version

# Verificar versão do Python
python --version

# Listar pacotes instalados
pip list

# Verificar conectividade com MinIO
ping minio

# Usar MinIO Client
mc alias set myminio http://minio:9000 minioadmin minioadmin
mc ls myminio
```

## Exemplos de Análise

### Criar DataFrame

```python
data = [
    (1, "João", 25),
    (2, "Maria", 30),
    (3, "Pedro", 22)
]

df = spark.createDataFrame(data, ["id", "nome", "idade"])
df.show()
```

### Transformações

```python
# Filtrar
df_filtered = df.filter(df.idade > 23)

# Selecionar colunas
df_selected = df.select("nome", "idade")

# Adicionar coluna
from pyspark.sql.functions import col
df_with_year = df.withColumn("ano_nascimento", 2025 - col("idade"))

# Agrupar
df_grouped = df.groupBy("idade").count()
```

### Análise com Pandas

```python
# Converter para Pandas
pdf = df.toPandas()

# Estatísticas
print(pdf.describe())

# Visualização
import matplotlib.pyplot as plt
pdf['idade'].plot(kind='hist')
plt.show()
```

## Troubleshooting

### Não consegue obter o token

```bash
# Execute este comando
docker logs spark-jupyter 2>&1 | grep token
```

### Spark UI não aparece

A Spark UI só fica disponível quando há um SparkSession ativo. Execute:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("test").getOrCreate()
```

Depois acesse: http://localhost:4040

### Erro ao conectar no MinIO

1. Verifique se MinIO está rodando: `docker ps | grep minio`
2. Verifique se estão na mesma network: `docker network inspect mybridge`
3. Teste conectividade: `docker exec spark-jupyter ping minio`

### Container trava no build

O build pode demorar ~10 minutos. Principais etapas:
1. Download do Spark (~400MB)
2. Download dos JARs (~100MB)
3. Instalação de pacotes Python

Se travar, pressione Ctrl+C e tente novamente.

### Erro de memória

Adicione no docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 4G
```

### Permissões de arquivo

```bash
# Linux/WSL
sudo chown -R $USER:$USER notebooks data config
chmod -R 755 notebooks data config
```

## Network Configuration

O Spark está configurado para usar a network externa `mybridge`:

```yaml
networks:
  mybridge:
    external: true
```

Esta network deve ser criada primeiro pelo MinIO. O Spark pode então acessar o MinIO usando o hostname `minio`.

## Performance Tips

### Otimizar Spark

```python
spark = SparkSession.builder \
    .appName("OptimizedApp") \
    .config("spark.executor.memory", "2g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()
```

### Cache de DataFrames

```python
df.cache()  # Mantém DataFrame em memória
df.persist()  # Persiste em disco/memória
```

### Particionar Dados

```python
df.write \
    .partitionBy("ano", "mes") \
    .parquet("s3a://dados/particionado/")
```

## Referências

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [PySpark API Reference](https://spark.apache.org/docs/latest/api/python/)
- [JupyterLab Documentation](https://jupyterlab.readthedocs.io/)
- [Delta Lake Guide](https://docs.delta.io/latest/index.html)
- [Hadoop-AWS Configuration](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/index.html)