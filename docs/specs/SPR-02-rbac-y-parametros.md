# SPR-02: módulo administrativo, seguridad y configuración inicial

- Estado: **implementado y verificado localmente; pendiente de revisión colaborativa y cierre mediante PR hacia `develop`**.
- Sprint: SPR-02.
- Responsable de especificación: equipo del proyecto.
- Rama prevista: `feature/rbac-y-parametros`.
- Última revisión funcional: 2026-09-10.

## 1. Propósito y límite del Sprint 2

El Sprint 2 entrega el cimiento administrativo del prototipo BI asistido por IA. Su objetivo no es producir análisis BI, ETL, tableros ni respuestas de IA: es permitir que una persona administradora gestione de manera comprensible y segura quién ingresa, qué puede hacer, qué opciones visualiza y qué configuraciones aprobadas utiliza la plataforma.

El alcance se divide deliberadamente en tres capacidades. Cada una tiene su propia especificación y criterios verificables; no se aceptará una interfaz que mezcle datos, formularios o estados de una capacidad con otra.

| Capacidad | Especificación normativa | Resultado esperado |
|---|---|---|
| Seguridad y RBAC | [SPR-02-01-seguridad-rbac.md](SPR-02-01-seguridad-rbac.md) | Usuarios, roles, permisos, menús y auditoría administrados sin exponer códigos internos ni bloquear la administración. |
| Navegación y UX | [SPR-02-02-navegacion-y-experiencia.md](SPR-02-02-navegacion-y-experiencia.md) | Cascarón responsive, menú lateral ocultable y grupos que siempre pueden plegarse o desplegarse. |
| Parámetros y LLM | [SPR-02-03-parametros-y-llm.md](SPR-02-03-parametros-y-llm.md) | Parámetros con propósito claro y configuración LLM separada, guiada y comprobable. |
| Identidad visual BI | [SPR-02-04-identidad-visual-y-shell-bi.md](SPR-02-04-identidad-visual-y-shell-bi.md) | Dirección visual común para el módulo administrativo, los datos, la analítica y el futuro copiloto. |
| Trazabilidad de correcciones | [SPR-02-matriz-correcciones.md](SPR-02-matriz-correcciones.md) | Cada observación recibida se relaciona con un requisito y una prueba. |

## 2. Principios obligatorios

1. **El backend autoriza.** Ocultar una acción o un menú en React mejora la experiencia, pero FastAPI valida siempre la sesión JWT y el permiso efectivo.
2. **La interfaz usa lenguaje de negocio.** Los identificadores técnicos (`security.users.write`, rutas, claves internas e identificadores numéricos) sirven al software y a soporte técnico; no son datos que la persona deba adivinar o digitar para administrar acceso.
3. **Cada pantalla conserva su propio estado.** Seleccionar "Editar rol" no puede poblar formularios de permisos, menús, parámetros ni LLM. Al cambiar de vista, se cancela la edición anterior. No se mostrará `undefined`, datos residuales ni referencias ajenas al recurso actual.
4. **La administración debe ser recuperable.** No se permitirá desactivar, vaciar de privilegios ni alterar la identidad técnica de la única vía administrativa protegida. El sistema debe rechazar una acción que deje a la plataforma sin al menos una cuenta activa con capacidad de recuperar la seguridad.
5. **Configuración no significa programación.** Un valor configurable sólo se muestra cuando tiene nombre humano, propósito, tipo, validación, consumidor conocido y auditoría. Crear valores, permisos, rutas o proveedores arbitrarios no vuelve al producto más flexible: lo vuelve inseguro y difícil de operar.
6. **Cada cambio administrativo se audita sin secretos.** Se registra actor, fecha, tipo de acción, recurso y resumen seguro; nunca contraseñas, JWT, claves API ni cadenas de conexión completas.

## 3. Alcance incluido

- Inicio de sesión con JWT de vida limitada, hash Argon2 y mensajes seguros.
- Consulta, creación y edición guiada de usuarios y asignación de uno o varios roles mediante selección por nombre.
- Consulta y administración protegida de roles y su conjunto de permisos mediante selección legible.
- Catálogo de permisos y de menús con nombres, descripciones y ayudas; las claves y rutas internas permanecen controladas por el software.
- Menú autorizado, agrupado y responsive; Inicio es acceso directo y no un grupo artificial.
- Bitácora de auditoría sólo de consulta.
- Catálogo de parámetros operativos aprobados y configuración independiente de un proveedor LLM; prueba de conexión desde el backend.
- Paginación, búsqueda y estados de carga, vacío, error, éxito y acceso denegado en las listas administrativas.

## 4. Exclusiones explícitas

- Recuperación de contraseña por correo, SSO institucional, multiempresa, microservicios y temas visuales configurables por empresa.
- ETL, metadatos, conexión universal a fuentes, datamart, dashboard BI, reportería funcional, predicciones y generación de consultas o modelos BI por LLM.
- Alta libre de permisos de aplicación, rutas o módulos desde la interfaz. Agregar una capacidad de software requerirá una especificación posterior, migración controlada y pruebas.
- Almacenamiento o visualización de contraseñas, tokens, claves de proveedores o cadenas de conexión completas en PostgreSQL o React.

## 5. Orden de construcción correctiva

1. Corregir el aislamiento de estado y las protecciones de recuperación administrativa.
2. Sustituir las entradas de IDs y códigos técnicos por catálogos seleccionables, ayudas y validaciones.
3. Aplicar la navegación lateral ocultable y el plegado libre de todos los grupos.
4. Separar definitivamente Parámetros generales de Configuración LLM, con sus pruebas y ayudas.
5. Completar pruebas de autorización negativa, interfaz, responsive y auditoría; luego actualizar bitácora, manual técnico y documentación del Sprint 2.

## 6. Condición de cierre

El Sprint 2 sólo se considerará cerrado cuando todos los criterios de aceptación de las tres especificaciones hijas estén aprobados, las observaciones de la matriz estén resueltas con evidencia, `make verify` sea exitoso dentro de Docker y las capturas de escritorio, tableta y móvil no exhiban estados cruzados, textos técnicos innecesarios ni pérdida de acceso administrativo.
