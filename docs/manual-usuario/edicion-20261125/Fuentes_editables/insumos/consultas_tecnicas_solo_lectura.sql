-- Consultas auxiliares autorizadas para documentación.
-- Solo definiciones de roles/permisos e identificadores técnicos de dos expedientes.
-- No consultar usuarios, credenciales, documentos JSON ni filas de tablas de ventas.
BEGIN READ ONLY;
SELECT version_num FROM public.alembic_version;
SELECT p.id AS proposal_id,p.status AS proposal_status,p.metadata_snapshot_id,
       e.id AS execution_id,e.status AS execution_status,
       e.metadata_snapshot_id AS execution_snapshot_id,
       e.metadata_snapshot_id=p.metadata_snapshot_id AS same_snapshot,
       s.data_connection_id,s.database_name,c.connector_kind
FROM app.bi_proposals p
JOIN app.etl_executions e ON e.proposal_id=p.id
JOIN app.metadata_snapshots s ON s.id=p.metadata_snapshot_id
JOIN app.data_connections c ON c.id=s.data_connection_id
WHERE (p.id=129 AND e.id=21) OR (p.id=131 AND e.id=22);
SELECT r.code AS role_code,r.name AS role_name,r.is_active AS role_active,
       p.code AS permission_code,p.name AS permission_name,p.is_active AS permission_active
FROM app.roles r
LEFT JOIN app.role_permissions rp ON rp.role_id=r.id
LEFT JOIN app.permissions p ON p.id=rp.permission_id
ORDER BY r.code,p.code;
ROLLBACK;
