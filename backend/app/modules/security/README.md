# Módulo de seguridad RBAC

Este módulo implementa autenticación JWT, usuarios, roles, permisos, menús autorizados y auditoría en el esquema PostgreSQL `app`. FastAPI es la autoridad de autorización: el frontend sólo representa las opciones que la sesión ya tiene permitidas.

## Protección administrativa

La cuenta inicial, el rol administrativo inicial y el catálogo de permisos/menús de sistema se marcan como `is_system_protected`. La API rechaza acciones que desactiven la cuenta o rol protegidos, o que retiren del rol administrativo los permisos mínimos para recuperar la gestión de Usuarios, Roles, Permisos y Menús. La protección no depende de un ID fijo ni de que React oculte un botón.

## Contrato de interfaz

Los roles se seleccionan por nombre y descripción al administrar usuarios. Los permisos se seleccionan por nombre y descripción al administrar roles o menús. Los identificadores numéricos y códigos técnicos se conservan sólo dentro del contrato API, migraciones y reglas de autorización; no se solicitan a la persona administradora como texto libre.

La especificación normativa está en [`docs/specs/SPR-02-01-seguridad-rbac.md`](../../../docs/specs/SPR-02-01-seguridad-rbac.md).
