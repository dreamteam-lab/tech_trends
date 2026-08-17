# Официальный образ SeaweedFS, версия закреплена (см. https://github.com/seaweedfs/seaweedfs/releases)
FROM chrislusf/seaweedfs:4.41

COPY s3-config.json.template /etc/seaweedfs/s3-config.json.template
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
