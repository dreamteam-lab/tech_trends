# Официальный образ Apache Spark, версия закреплена.
# Тег содержит Scala 2.13 / Java 17 / Python (для pyspark) на базе Ubuntu.
FROM apache/spark:4.1.3-scala2.13-java17-python3-r-ubuntu

USER root

# curl нужен только на этапе сборки — скачать JAR-зависимости для S3A
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# hadoop-aws + AWS SDK для доступа к S3A.
#
# ВАЖНО: начиная с Hadoop 3.4.2 проект перешёл с AWS SDK v1 (com.amazonaws:aws-java-sdk-bundle)
# на AWS SDK v2 (software.amazon.awssdk:bundle) для модуля S3A. Hadoop сознательно НЕ публикует
# этот бандл как обычную maven-зависимость (файл ~500MB) — версию нужно вручную сверять
# с официальными release notes: https://hadoop.apache.org/release/<version>.html
#
# Поэтому версии здесь закреплены явно (а не вычисляются автоматически из pom.xml, как для
# более старых версий Hadoop) — но сборка проверяет, что версия Hadoop в базовом образе Spark
# совпадает с той, под которую подобран AWS SDK. Если базовый образ обновится на другой Hadoop —
# сборка упадёт здесь с понятной ошибкой, а не тихо соберёт несовместимые JAR.
RUN set -eu; \
    HADOOP_JAR=$(find /opt/spark/jars -maxdepth 1 -name 'hadoop-client-api-*.jar' | head -n1); \
    if [ -z "$HADOOP_JAR" ]; then \
        echo "ERROR: hadoop-client-api-*.jar not found in /opt/spark/jars — базовый образ мог измениться"; \
        exit 1; \
    fi; \
    HADOOP_VERSION=$(basename "$HADOOP_JAR" | sed -E 's/hadoop-client-api-(.*)\.jar/\1/'); \
    echo "Detected bundled Hadoop version: $HADOOP_VERSION"; \
    \
    EXPECTED_HADOOP_VERSION="3.4.2"; \
    AWS_SDK_V2_BUNDLE_VERSION="2.35.4"; \
    if [ "$HADOOP_VERSION" != "$EXPECTED_HADOOP_VERSION" ]; then \
        echo "ERROR: базовый образ Spark содержит Hadoop $HADOOP_VERSION, а закреплена связка под $EXPECTED_HADOOP_VERSION."; \
        echo "Сверься с https://hadoop.apache.org/release/ и обнови EXPECTED_HADOOP_VERSION / AWS_SDK_V2_BUNDLE_VERSION в этом Dockerfile."; \
        exit 1; \
    fi; \
    \
    curl -fsSL -o "/opt/spark/jars/hadoop-aws-${HADOOP_VERSION}.jar" \
        "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar"; \
    curl -fsSL -o "/opt/spark/jars/bundle-${AWS_SDK_V2_BUNDLE_VERSION}.jar" \
        "https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/${AWS_SDK_V2_BUNDLE_VERSION}/bundle-${AWS_SDK_V2_BUNDLE_VERSION}.jar"

COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf

USER spark
