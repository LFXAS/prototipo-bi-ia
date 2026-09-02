# SPR-02: seguridad RBAC y parámetros de conexión

- Estado: borrador
- Sprint: SPR-02
- Responsable de especificación: equipo del proyecto
- Rama prevista: `feature/rbac-y-parametros`
- Fecha de creación: 2026-09-01
- PR de implementación: pendiente

## 1. Problema y objetivo

El prototipo necesita un módulo mínimo de seguridad exigido académicamente y un mecanismo auditable para parametrizar conexiones. El objetivo es que un administrador pueda gestionar usuarios, roles, permisos, menús y parámetros aprobados, mientras FastAPI autoriza todas las operaciones relevantes.

## 2. Alcance y exclusiones

- Incluido: migración inicial PostgreSQL, usuarios, roles, permisos, asignaciones, menús, auditoría, autenticación y autorización mínima; parámetros de conexión sin secretos visibles en la interfaz; prueba controlada de acceso lector a AdventureWorks.
- Excluido: SSO institucional, recuperación de contraseña por correo, administración avanzada multiempresa, conectores universales, introspección automática y ETL.

## 3. Actores, flujo y reglas

- Administrador: crea o desactiva usuarios, asigna roles y permisos, administra menús y parámetros permitidos.
- Usuario autenticado: sólo ve menús autorizados y sólo puede llamar endpoints cuyo permiso posea.
- Backend: deniega por defecto. Ocultar un menú en React nunca sustituye la autorización del backend.
- Fuente SQL Server: se usa exclusivamente con la cuenta lectora; ningún endpoint permitirá ejecutar escritura en AdventureWorks.

## 4. Datos, API e interfaz

- Migraciones: `app.users`, `app.roles`, `app.permissions`, `app.user_roles`, `app.role_permissions`, `app.menus`, `app.menu_permissions`, `app.audit_events` y parámetros necesarios.
- API prevista: autenticación, sesión actual, administración mínima RBAC, menú autorizado y prueba de conexión aprobada.
- Interfaz prevista: inicio de sesión, pantalla administrativa mínima y menú dinámico. No incluye dashboard BI en este sprint.

## 5. Seguridad y auditoría

- Contraseñas con Argon2 o bcrypt; nunca texto plano.
- JWT de vida limitada; secretos sólo por variables de entorno.
- Autorización por códigos estables de permiso en FastAPI.
- Auditoría de inicio de sesión, cambios de roles/permisos, cambios de parámetros y pruebas de conexión.
- Los secretos de conexión no se devuelven por API ni se registran en texto claro.

## 6. Criterios de aceptación verificables

- [ ] Una migración limpia crea todas las tablas RBAC y de parámetros en el esquema `app`.
- [ ] Un usuario con rol autorizado puede iniciar sesión y consultar sólo sus menús.
- [ ] Un usuario sin permiso recibe respuesta de autorización denegada aunque intente llamar el endpoint directamente.
- [ ] La interfaz no muestra menús sin permiso, pero la decisión real se toma en FastAPI.
- [ ] Una prueba de conexión usa el lector de AdventureWorks y no revela secretos.
- [ ] Los cambios administrativos y pruebas de conexión quedan en `audit_events`.
- [ ] Pruebas de backend, frontend, migraciones y CI pasan dentro de Docker.

## 7. Plan de pruebas y evidencia

Pruebas unitarias de hash y autorización; integración con PostgreSQL para migraciones y auditoría; pruebas de interfaz para menú; una evidencia de CI verde y capturas sin secretos para la tesis. Antes de cerrar el PR se ejecutará `make verify` y los PDF/documentos afectados se regenerarán.

## 8. Riesgos, dependencias y decisiones

Depende de Alembic y de los límites modulares existentes. El diseño exacto de JWT, hashes y entidades deberá documentarse en un ADR si introduce una decisión que afecte sprints posteriores. Las cuentas iniciales y sus credenciales no se versionarán.

## 9. Resultado de implementación

Pendiente. Se completará con PR, SHA, evidencia de CI, resultados de pruebas y enlace a la bitácora cuando el sprint se ejecute.
