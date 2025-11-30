# Dockerfile otimizado - Spark + Jupyter + MinIO
FROM jupyter/base-notebook:latest

ENV SPARK_VERSION=3.5.7 \
    HADOOP_VERSION=3 \
    SPARK_HOME=/usr/local/spark \
    PATH=/usr/local/spark/bin:$PATH

USER root

# Instala Java, Spark e ferramentas essenciais
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-11-jdk wget curl && \
    wget --no-check-certificate https://downloads.apache.org/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop$HADOOP_VERSION.tgz -O /tmp/spark.tgz && \
    tar xzvf /tmp/spark.tgz -C /usr/local/ && \
    mv /usr/local/spark-$SPARK_VERSION-bin-hadoop$HADOOP_VERSION $SPARK_HOME && \
    rm /tmp/spark.tgz && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Bibliotecas Python para análise de dados
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    pyspark==${SPARK_VERSION} \
    pandas \
    seaborn \
    matplotlib \
    boto3 \
    delta-spark==3.2.1

# JARs essenciais para MinIO/S3
RUN wget --no-check-certificate -q https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar -P /usr/local/spark/jars/ && \
    wget --no-check-certificate -q https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar -P /usr/local/spark/jars/

# JARs para Delta Lake (tabelas ACID)
RUN wget --no-check-certificate -q https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar -P /usr/local/spark/jars/ && \
    wget --no-check-certificate -q https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar -P /usr/local/spark/jars/

# JAR para formato Avro
#RUN wget --no-check-certificate -q https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/${SPARK_VERSION}/spark-avro_2.12-${SPARK_VERSION}.jar -P /usr/local/spark/jars/

# MinIO Client (para gerenciar buckets via CLI)
RUN wget --no-check-certificate -q https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/local/bin/mc && \
    chmod +x /usr/local/bin/mc

# Permissões sudo para o usuário jovyan
RUN echo "jovyan ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/jovyan

USER jovyan
WORKDIR /home/jovyan/work