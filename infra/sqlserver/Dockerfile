# syntax=docker/dockerfile:1.7
FROM mcr.microsoft.com/mssql/server:2022-latest AS production

USER root
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh bootstrap-adventureworks.sh /usr/local/bin/
RUN chmod 0755 /usr/local/bin/entrypoint.sh /usr/local/bin/bootstrap-adventureworks.sh \
    && mkdir -p /var/opt/mssql/backup \
    && chown -R mssql:root /var/opt/mssql/backup

USER mssql
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/opt/mssql/bin/sqlservr"]
