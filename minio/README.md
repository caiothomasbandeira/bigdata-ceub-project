# MinIO - Object Storage (Data Lake)

MinIO é um servidor de armazenamento de objetos compatível com S3, usado neste projeto como Data Lake para armazenar dados brutos e processados.

## Configuração

### Estrutura de Diretórios

```
minio/
├── docker-compose.yml       # Configuração do container
├── minio-data/             # Volume para dados persistentes
└── minio-backup/           # Volume para backups
```

### Especificações do Container

- **Imagem:** `minio/minio:latest`
- **Container Name:** `minio`
- **Network:** `mybridge` (compartilhada com Spark)

### Portas Expostas

- **9000:** MinIO API (S3-compatible)
- **9001:** MinIO Console (Interface Web)

### Credenciais Padrão

- **Access Key:** `minioadmin`
- **Secret Key:** `minioadmin`

### Variáveis de Ambiente

```yaml
MINIO_ROOT_USER: minioadmin
MINIO_ROOT_PASSWORD: minioadmin
```

## Como Rodar

### Iniciar o Container

```bash
# No diretório minio/
docker compose up -d
```

### Verificar Status

```bash
# Ver logs
docker logs minio

# Ver status do container
docker ps | grep minio
```

### Parar o Container

```bash
# Parar e remover container e network
docker compose down

# Parar sem remover
docker compose stop
```

### Reiniciar o Container

```bash
docker compose restart
```

## Acessar Interface Gráfica

### MinIO Console (Web UI)

1. **URL:** http://localhost:9001
2. **Login:**
   - Username: `minioadmin`
   - Password: `minioadmin`

### Funcionalidades da Interface

#### 1. Buckets
- Criar novos buckets
- Visualizar objetos armazenados
- Upload/Download de arquivos
- Configurar políticas de acesso

#### 2. Object Browser
- Navegar pela estrutura de pastas
- Visualizar metadados dos objetos
- Fazer download de arquivos
- Deletar objetos

#### 3. Access Keys
- Criar chaves de acesso adicionais
- Gerenciar permissões
- Rotacionar credenciais

#### 4. Monitoring
- Métricas de uso
- Espaço em disco
- Requisições por segundo

## Criar Bucket via Interface

1. Acesse http://localhost:9001
2. Faça login com `minioadmin` / `minioadmin`
3. Clique em **"Buckets"** no menu lateral
4. Clique em **"Create Bucket"**
5. Digite o nome do bucket (exemplo: `dados`)
6. Clique em **"Create"**

## Acessar via API (S3)

### Endpoint Configuration

```
Endpoint: http://minio:9000  (dentro do Docker)
Endpoint: http://localhost:9000  (fora do Docker)
Access Key: minioadmin
Secret Key: minioadmin
Region: us-east-1
```

### Exemplo Python (boto3)

```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    region_name='us-east-1'
)

# Listar buckets
response = s3.list_buckets()
print(response['Buckets'])
```

### Exemplo PySpark

```python
spark = SparkSession.builder \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# Ler dados
df = spark.read.parquet("s3a://dados/caminho/arquivo.parquet")
```

## MinIO Client (mc)

O MinIO Client é uma ferramenta CLI para gerenciar o MinIO.

### Instalar mc (Opcional)

```bash
# Linux/MacOS
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://dl.min.io/client/mc/release/windows-amd64/mc.exe" -OutFile "mc.exe"
```

### Configurar Alias

```bash
mc alias set myminio http://localhost:9000 minioadmin minioadmin
```

### Comandos Úteis

```bash
# Listar buckets
mc ls myminio

# Criar bucket
mc mb myminio/dados

# Upload arquivo
mc cp arquivo.csv myminio/dados/

# Download arquivo
mc cp myminio/dados/arquivo.csv ./

# Remover arquivo
mc rm myminio/dados/arquivo.csv

# Sincronizar diretório
mc mirror ./local-dir myminio/dados/remote-dir
```

## Volumes Persistentes

### minio-data
- **Descrição:** Armazena todos os objetos e metadados
- **Path no Container:** `/data`
- **Path no Host:** `./minio-data`

### minio-backup
- **Descrição:** Diretório para armazenar backups
- **Path no Container:** `/backup`
- **Path no Host:** `./minio-backup`

## Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker logs minio --tail 100

# Verificar se porta está em uso
netstat -ano | findstr :9000
netstat -ano | findstr :9001
```

### Não consegue acessar a interface

1. Verifique se o container está rodando: `docker ps`
2. Verifique os logs: `docker logs minio`
3. Tente acessar: http://127.0.0.1:9001
4. Verifique firewall/antivírus

### Erro de permissão nos volumes

```bash
# Linux/WSL
sudo chown -R $USER:$USER minio-data minio-backup
chmod -R 755 minio-data minio-backup
```

### Resetar completamente

```bash
# ATENÇÃO: Isso apaga todos os dados!
docker compose down
rm -rf minio-data/*
docker compose up -d
```

## Network Configuration

O MinIO está configurado na network `mybridge` para comunicação com o Spark:

```yaml
networks:
  mybridge:
    name: mybridge
    driver: bridge
```

Esta network permite que o Spark acesse o MinIO usando o hostname `minio:9000`.

## Comandos Docker Úteis

```bash
# Ver logs em tempo real
docker logs -f minio

# Acessar shell do container
docker exec -it minio sh

# Ver uso de recursos
docker stats minio

# Inspecionar container
docker inspect minio

# Ver informações da network
docker network inspect mybridge

# Backup manual
docker exec minio mc mirror /data /backup
```

## Integração com Spark

O Spark pode acessar o MinIO usando o protocolo S3A:

- **Endpoint:** `http://minio:9000` (nome do container na network)
- **Access Key:** `minioadmin`
- **Secret Key:** `minioadmin`

Exemplo de URL: `s3a://nome-bucket/caminho/arquivo.parquet`

## Referências

- [Documentação MinIO](https://min.io/docs/minio/linux/index.html)
- [MinIO Client Guide](https://min.io/docs/minio/linux/reference/minio-mc.html)
- [S3 API Compatibility](https://docs.min.io/docs/minio-server-limits-per-tenant.html)