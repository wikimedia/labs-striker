FROM docker.io/mariadb:10.4

ENV MARIADB_INITDB_SKIP_TZINFO=0 \
    MARIADB_ROOT_PASSWORD=root

COPY docker-entrypoint-initdb.d /docker-entrypoint-initdb.d/

CMD ["--character-set-server=utf8mb4", "--collation-server=utf8mb4_unicode_ci", "--local-infile=0", "--max-allowed-packet=32M", "--innodb-buffer-pool-size=256MB", "--sql-mode=STRICT_ALL_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION"]
