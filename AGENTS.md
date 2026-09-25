# 🤖 Reglas de Conducta y Calidad para Agentes de IA (AGENTS.md)

Este documento define las directrices obligatorias, protocolos de calidad y normas de conducta para cualquier agente de IA (Antigravity, Cline, Roo Code, GitHub Copilot Workspace, etc.) que trabaje en este proyecto.

---

## 🏗️ 1. Identidad y Stack Tecnológico del Proyecto

**AutoERP** es una plataforma integral de gestión ERP para talleres mecánicos y de servicio automotriz.

El proyecto está estructurado en los siguientes módulos principales:
- **Backend API (`BE/`):**
  - **Lenguaje / Framework:** Python 3.10+, FastAPI
  - **ORM & Migraciones:** SQLAlchemy 2.0+, Alembic
  - **Base de Datos:** PostgreSQL
  - **Validación & Schemas:** Pydantic v2
  - **Repositorio Git:** `AngelGongora92/autoerp-api`

- **Frontend WebApp (`FE/`):**
  - **Lenguaje / Framework:** React 18+, Vite, JavaScript / JSX
  - **Estilos:** Tailwind CSS / Vanilla CSS
  - **Herramientas de Build:** Vite, ESLint
  - **Repositorio Git:** `AngelGongora92/autoerp_fe_1.0`

---

## 🚫 2. Prohibición Absoluta de Merges Directos

1. **PROHIBIDO** hacer `git merge` directo o `git push` a las ramas protegidas `main` o `dev` desde la terminal.
2. **Flujo de Ramas Obligatorio:**
   - Toda nueva tarea o bugfix debe desarrollarse en su propia rama descriptiva creada a partir de `dev` (o `main` en su defecto), con el formato `feat/<ticket_id>-<descripcion-corta>` o `fix/<ticket_id>-<descripcion-corta>`.
3. **Verificación Previa a la Entrega:**
   - Antes de abrir un Pull Request, se debe ejecutar y aprobar la suite de pruebas y compilación correspondiente:
     - Backend: `pytest` / comprobación de servidor FastAPI y migraciones con Alembic.
     - Frontend: `npm run build` y validación de linter.
4. **Entrega mediante Pull Request (PR):**
   - El agente debe entregar su trabajo creando un Pull Request en GitHub mediante el CLI de GitHub:
     ```bash
     gh pr create --base dev --title "feat(scope): <descripcion>" --body "<detalles>"
     ```
   - **El usuario humano es la única persona autorizada para revisar, aprobar y fusionar (merge) el Pull Request en la interfaz web de GitHub.**

---

## 📋 3. Protocolo OpenSpec

Antes de comenzar la fase de codificación de cualquier ticket o requerimiento:

1. **Lectura de Especificaciones:**
   - El agente DEBE consultar y leer detenidamente la especificación activa en `openspec/changes/<ticket_id>/`:
     - `proposal.md`: Explicación del problema, contexto e impacto arquitectónico.
     - `spec.md`: Requerimientos funcionales, contratos de datos y criterios de aceptación.
     - `tasks.md`: Lista paso a paso de subtareas a ejecutar.
2. **Seguimiento de Progreso:**
   - Conforme el agente complete cada subtarea de `tasks.md`, debe actualizar el archivo marcando la casilla correspondiente `[x]`.
3. **Archivado al Finalizar:**
   - Una vez completado el ticket, aprobado el PR e integrado el código, la carpeta de la especificación en `openspec/changes/<ticket_id>/` debe mover a `openspec/changes/archive/<ticket_id>/`.

---

## 🛠️ 4. Autonomía, Diagnóstico y Manejo de Errores

1. **Diagnóstico Basado en Logs Reales:**
   - Ante cualquier falla o excepción en tiempo de ejecución o pruebas, la PRIMERA acción del agente debe ser inspeccionar los logs completos sin asumir causas sin evidencia.
2. **Prohibición de Parches Superficiales:**
   - **PROHIBIDO** silenciar excepciones con `try/except: pass` vacíos, retornar datos dummy ficticios en producción para enmascarar errores, o comentar tests que fallan.
   - El agente debe solucionar la causa raíz del problema respetando la arquitectura del proyecto.
3. **Preservación de Comentarios y Contratos:**
   - Mantener intactos los comentarios relevantes y docstrings existentes. No alterar firmas de funciones ni estructuras de API existentes sin actualizar todos los sitios donde se invocan.

---

## 🔔 5. Notificación Temprana de Acciones Manuales

Si para completar la tarea se requieren acciones que escapan a la autonomía del agente (como configurar secretos en GitHub, crear variables de entorno `.env`, registrar webhooks o modificar paneles externos en Linear/Vercel/Supabase):

- El agente **DEBE notificar al usuario explícitamente al inicio o en cuanto se identifique la necesidad**, listando paso a paso los valores y la ubicación exacta de las configuraciones manuales requeridas.

---

## 🗄️ 6. Protocolo y Seguridad en Base de Datos y Migraciones (PostgreSQL + Alembic)

1. **Uso Obligatorio de Alembic para Modificaciones de Esquema:**
   - **PROHIBIDO** confiar únicamente en `Base.metadata.create_all()` para modificar esquemas en producción o desarrollo. SQLAlchemy NO altera ni añade columnas a tablas físicas ya existentes.
   - Cualquier adición, eliminación o modificación de columnas/tablas en los modelos de SQLAlchemy (`BE/api/database.py` o modelos del BE) exige generar un script de migración con Alembic: `alembic revision --autogenerate -m "<descripcion_ticket>"`.

2. **Prevención de Incompatibilidades y Corrupción de Datos (Buenas Prácticas de BD):**
   - **Cero Pérdida de Datos:** Queda estrictamente prohibido eliminar columnas o tablas físicas que contengan datos históricos activos sin la aprobación explícita y documentada del usuario.
   - **Adición Segura de Columnas:** Al agregar columnas a tablas preexistentes con datos, la columna DEBE ser opcional (`nullable=True`) o contar con un valor por defecto en servidor (`server_default="..."` o un paso intermedio que pueble los registros antiguos) para evitar fallos de restricción `NOT NULL`.
   - **Compatibilidad Hacia Atrás:** Modificaciones de tipos de datos o renombrado de campos deben garantizar la integridad previa y reflejarse adecuadamente tanto en `upgrade()` como en `downgrade()`.

3. **Verificación Previa a Subir Ramas y Abrir PRs:**
   - Ejecutar y verificar `alembic heads` para confirmar que no existan múltiples cabezas ni conflictos en el historial de revisiones.
   - Probar `alembic upgrade head` localmente para asegurar que la migración corre limpiamente sin errores SQL ni de sintaxis.

4. **Sincronización Automática en Despliegues de Producción:**
   - El backend ejecuta automáticamente `alembic upgrade head` durante el inicio de FastAPI (`app.on_event("startup")`). Esto asegura que cuando se haga merge a `main` y Vercel redespliegue, la base de datos de producción (Supabase) se actualice sin requerir ejecuciones manuales por consola.

