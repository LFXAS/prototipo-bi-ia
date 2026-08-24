#!/usr/bin/env bash
set -euo pipefail

: "${MSSQL_SA_PASSWORD:?MSSQL_SA_PASSWORD is required}"

database="${SQLSERVER_DATABASE:-AdventureWorks2022}"
reader_user="${SQLSERVER_USER:-bi_reader}"
reader_password="${SQLSERVER_PASSWORD:-ChangeMe_Reader_2026!}"
backup_url="${ADVENTUREWORKS_BACKUP_URL:-https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks2022.bak}"
backup_path="/var/opt/mssql/backup/AdventureWorks2022.bak"
ready_file="/var/opt/mssql/.adventureworks-ready"
sqlcmd="/opt/mssql-tools18/bin/sqlcmd"

if [[ ! "${database}" =~ ^[A-Za-z0-9_]+$ ]]; then
    echo "SQLSERVER_DATABASE contains unsupported characters" >&2
    exit 1
fi

if [[ ! "${reader_user}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "SQLSERVER_USER contains unsupported characters" >&2
    exit 1
fi

if [[ ! "${reader_password}" =~ ^[A-Za-z0-9_@#%+=:,.!?-]{12,128}$ ]]; then
    echo "SQLSERVER_PASSWORD must be 12-128 safe characters" >&2
    exit 1
fi

rm -f "${ready_file}"

for attempt in $(seq 1 90); do
    if "${sqlcmd}" -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C -Q "SELECT 1" -b -o /dev/null; then
        break
    fi
    if [[ "${attempt}" -eq 90 ]]; then
        echo "SQL Server did not become available" >&2
        exit 1
    fi
    sleep 2
done

database_exists=$("${sqlcmd}" -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C -h -1 -W \
    -Q "SET NOCOUNT ON; SELECT CASE WHEN DB_ID(N'${database}') IS NULL THEN 0 ELSE 1 END")

if [[ "${database_exists}" == "0" ]]; then
    if [[ ! -s "${backup_path}" ]]; then
        echo "Downloading the official AdventureWorks2022 backup..."
        curl --fail --location --retry 5 --output "${backup_path}.part" "${backup_url}"
        mv "${backup_path}.part" "${backup_path}"
    fi

    echo "Restoring ${database}..."
    "${sqlcmd}" -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C -b -Q "
RESTORE DATABASE [${database}]
FROM DISK = N'${backup_path}'
WITH
    MOVE N'AdventureWorks2022' TO N'/var/opt/mssql/data/${database}.mdf',
    MOVE N'AdventureWorks2022_log' TO N'/var/opt/mssql/data/${database}_log.ldf',
    FILE = 1,
    RECOVERY,
    STATS = 10;"
fi

# The SQL Server listener can accept connections before an existing user
# database has finished recovery after a container restart. Wait for the
# actual source database before configuring the read-only account or marking
# the service as ready.
for attempt in $(seq 1 90); do
    if "${sqlcmd}" -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C \
        -d "${database}" -Q "SELECT 1" -b -o /dev/null; then
        break
    fi
    if [[ "${attempt}" -eq 90 ]]; then
        echo "${database} did not become available" >&2
        exit 1
    fi
    sleep 2
done

"${sqlcmd}" -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C -b \
    -v DatabaseName="${database}" ReaderUser="${reader_user}" ReaderPassword="${reader_password}" <<'SQL'
IF SUSER_ID(N'$(ReaderUser)') IS NULL
BEGIN
    EXEC(N'CREATE LOGIN [' + '$(ReaderUser)' + N'] WITH PASSWORD = N''' + '$(ReaderPassword)' + N''', CHECK_POLICY = ON;');
END;
GO

USE [$(DatabaseName)];
GO

IF USER_ID(N'$(ReaderUser)') IS NULL
BEGIN
    CREATE USER [$(ReaderUser)] FOR LOGIN [$(ReaderUser)];
END;
GO

IF IS_ROLEMEMBER(N'db_datareader', N'$(ReaderUser)') <> 1
BEGIN
    ALTER ROLE [db_datareader] ADD MEMBER [$(ReaderUser)];
END;
-- Remove overly broad denies from any previous bootstrap revision. In SQL
-- Server, DENY CONTROL also denies subordinate permissions such as CONNECT.
REVOKE CONTROL TO [$(ReaderUser)];
REVOKE ALTER TO [$(ReaderUser)];
DENY INSERT, UPDATE, DELETE, EXECUTE TO [$(ReaderUser)];
GO
SQL

touch "${ready_file}"
echo "${database} is ready with read-only login ${reader_user}."
