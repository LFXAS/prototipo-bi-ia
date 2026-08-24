\set ON_ERROR_STOP on

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS mart;

COMMENT ON SCHEMA app IS 'Seguridad, parametros, auditoria y ejecuciones del prototipo';
COMMENT ON SCHEMA mart IS 'Hechos y dimensiones del datamart demostrativo';
